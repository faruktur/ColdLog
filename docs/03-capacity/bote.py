#!/usr/bin/env python3
"""
FleetStream BOTE modeli.

Kullanim:  python bote.py
           python bote.py --test      (dokumandaki sayilari dogrula)

Asagidaki GIRDILER blogundaki sayilari degistir, calistir, tabloyu oku.
Her cikti satirinin formulu kodda gorunur durumda -- dokumandaki
03-capacity/bote-model.md ile ayni formuller.

Bu dosya tek basina modelin kendisi degil; modelin HESAP MAKINESI.
Gerekceler ve kararlar bote-model.md icinde.
"""
import math
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ----------------------------------------------------------------------
# GIRDILER  (kurcalanacak yer burasi)
# ----------------------------------------------------------------------
ASSET = 100_000           # S-01  takip edilen Asset sayisi
ORNEKLEME_SN = 5          # S-02  Asset basina bir Reading kac saniyede
PAYLOAD_B = 200           # 2.1   Reading'in tel uzerindeki boyutu (JSON ~200, Protobuf ~50)
KURAL = 7                 # C-01  Asset Type basina aktif kural sayisi
TEPE = 2                  # S-05  tepe faktoru (ortalamanin kac kati kapasite kuruldu)

KAFKA_RETENTION_GUN = 7   # 2.3   log'da ne kadar geriye gidilebilir
REPLICATION = 3           # 2.3   Kafka replication factor
PARTITION = 48            # B-04

HAM_RETENTION_GUN = 90    # R-01  cold path'te ham Reading saklama
SIKISTIRMA = 15           # 2.10  columnar + time-series sikistirma orani

POD_KAPASITE_RPS = 5_000  # 2.7   bir ingest pod'unun kaldirdigi req/sn (TAHMIN - Adim 7'de olculecek)
EVENT_ISLEME_US = 20      # 2.6   event basina stream processing suresi (TAHMIN - Adim 7'de olculecek)
STATE_OVERHEAD = 1.2      # 2.4   dictionary / object header payi

DOMAIN_BUTCE_SN = 180     # 1.1   15 dk toplam butceden sisteme kalan (3 dk)
KESINTI_SN = 24 * 3600    # 2.8   senaryo: ne kadarlik bir kesintiden toparlaniyoruz
PENCERE_SN = 600          # 2.4   (b) modelindeki pencere suresi
KOVA_SN = 60              # 2.4   (b) modelinin kovalanmis halinde kova boyu
LATE_DATA_SN = 24 * 3600  # D-03  kabul edilen maksimum gec veri


# ----------------------------------------------------------------------
# MODEL
# ----------------------------------------------------------------------
def model(**ov):
    g = dict(
        asset=ASSET, ornekleme=ORNEKLEME_SN, payload=PAYLOAD_B, kural=KURAL,
        tepe=TEPE, kafka_gun=KAFKA_RETENTION_GUN, rf=REPLICATION, partition=PARTITION,
        ham_gun=HAM_RETENTION_GUN, sikistirma=SIKISTIRMA,
        pod_rps=POD_KAPASITE_RPS, isleme_us=EVENT_ISLEME_US, overhead=STATE_OVERHEAD,
        butce_sn=DOMAIN_BUTCE_SN, kesinti_sn=KESINTI_SN,
        pencere_sn=PENCERE_SN, kova_sn=KOVA_SN, late_sn=LATE_DATA_SN,
    )
    g.update(ov)
    r = {}

    # --- olcek ---
    r["eps"] = g["asset"] / g["ornekleme"]                      # S-03
    r["gunluk_event"] = r["eps"] * 86_400                       # S-04
    r["tepe_eps"] = r["eps"] * g["tepe"]
    r["degerlendirme_eps"] = r["eps"] * g["kural"]              # C-01

    # --- bant genisligi ---
    r["mb_sn"] = r["eps"] * g["payload"] / 1e6
    r["tepe_mb_sn"] = r["tepe_eps"] * g["payload"] / 1e6
    r["mbit_sn"] = r["mb_sn"] * 8

    # --- Kafka ---
    r["gunluk_gb"] = r["gunluk_event"] * g["payload"] / 1e9
    r["kafka_tb"] = r["gunluk_gb"] * g["kafka_gun"] * g["rf"] / 1000
    r["partition_eps"] = r["eps"] / g["partition"]
    r["partition_kb_sn"] = r["partition_eps"] * g["payload"] / 1e3

    # --- state: (a) esik + surekli sure -> SONUC saklanir, veri saklanmaz ---
    # Asset+kural basina: streak_start (8B) + fired flag + hizalama  = 16B
    # ayrica Asset basina son bilinen durum (lat/lon/speed/temp/humidity/last_seen) = 100B
    r["state_a_mb"] = (g["asset"] * g["kural"] * 16 + g["asset"] * 100) * g["overhead"] / 1e6

    # --- state: (b) pencere ortalamasi, HAM veri saklanarak ---
    # pencereden cikan okumayi ortalamadan dusmek icin degerini bilmek sart
    r["pencere_reading"] = g["pencere_sn"] / g["ornekleme"]
    r["state_b_ham_mb"] = r["pencere_reading"] * g["payload"] * g["asset"] * g["overhead"] / 1e6

    # --- state: (b') ayni kural, kovalanmis (her kovada sum+count) ---
    r["kova_sayisi"] = g["pencere_sn"] / g["kova_sn"]
    r["state_b_kova_mb"] = r["kova_sayisi"] * 16 * g["kural"] * g["asset"] * g["overhead"] / 1e6

    # --- state: (c) gec veriyi CANLI STATE uzerinden karsilamak ---
    # 24 saat geriye donuk hesap yapabilmek icin 24 saatlik tum Reading'ler
    r["late_reading"] = g["late_sn"] / g["ornekleme"]
    r["state_c_gb"] = r["late_reading"] * g["payload"] * g["asset"] * g["overhead"] / 1e9

    r["state_c_a_orani"] = r["state_c_gb"] * 1000 / r["state_a_mb"]

    # --- CPU ---
    r["core"] = r["eps"] * g["isleme_us"] / 1e6
    r["tepe_core"] = r["tepe_eps"] * g["isleme_us"] / 1e6

    # --- ingest pod ---
    r["pod_ort"] = math.ceil(r["eps"] / g["pod_rps"])
    r["pod_tepe"] = math.ceil(r["tepe_eps"] / g["pod_rps"])
    r["pod"] = r["pod_tepe"] + 1                                 # N+1
    r["pod_basina_baglanti"] = g["asset"] / r["pod"]

    # --- cold path ---
    r["ham_satir"] = r["gunluk_event"] * g["ham_gun"]
    r["ham_tb"] = r["gunluk_gb"] * g["ham_gun"] / 1000
    r["sikis_tb"] = r["ham_tb"] / g["sikistirma"]

    # --- recovery burst ---
    r["backlog"] = r["eps"] * g["kesinti_sn"]
    r["fazla_kapasite_eps"] = r["eps"] * (g["tepe"] - 1)
    r["yakalama_sn"] = (g["kesinti_sn"] / (g["tepe"] - 1)) if g["tepe"] > 1 else float("inf")

    # --- SLO bozulma payi ---
    r["pay_5sn"] = g["butce_sn"] / 5
    r["pay_60sn"] = g["butce_sn"] / 60
    r["pay_300sn"] = g["butce_sn"] / 300
    return r


def sn(x):
    """saniyeyi okunur hale getir"""
    if x == float("inf"):
        return "asla"
    if x < 60:
        return f"{x:.0f} sn"
    if x < 3600:
        return f"{x/60:.0f} dk"
    if x < 86_400:
        return f"{x/3600:.1f} saat"
    return f"{x/86_400:.1f} gun"


def rapor():
    r = model()
    p = print
    p("=" * 68)
    p(f"FleetStream BOTE   |  {ASSET:,} Asset  x  1 Reading/{ORNEKLEME_SN} sn  x  {PAYLOAD_B} B")
    p("=" * 68)

    p("\n-- OLCEK -------------------------------------------------------")
    p(f"  ingest hizi (ortalama)        {r['eps']:>14,.0f} event/sn")
    p(f"  ingest hizi (tepe x{TEPE})         {r['tepe_eps']:>14,.0f} event/sn")
    p(f"  gunluk event                  {r['gunluk_event']:>14,.0f}")
    p(f"  kural degerlendirmesi         {r['degerlendirme_eps']:>14,.0f} /sn   ({KURAL} kural)")

    p("\n-- BANT GENISLIGI ----------------------------------------------")
    p(f"  ortalama                      {r['mb_sn']:>14,.1f} MB/sn  (~{r['mbit_sn']:,.0f} Mbit/sn)")
    p(f"  tepe                          {r['tepe_mb_sn']:>14,.1f} MB/sn")

    p("\n-- KAFKA -------------------------------------------------------")
    p(f"  gunluk hacim                  {r['gunluk_gb']:>14,.0f} GB/gun")
    p(f"  disk ({KAFKA_RETENTION_GUN} gun x RF{REPLICATION})           {r['kafka_tb']:>14,.1f} TB")
    p(f"  partition basina ({PARTITION})          {r['partition_eps']:>14,.0f} event/sn"
      f"   ({r['partition_kb_sn']:,.0f} KB/sn)")

    p("\n-- STREAM PROCESSING STATE -------------------------------------")
    p(f"  (a) esik + surekli sure       {r['state_a_mb']:>14,.0f} MB     <-- SONUC saklanir")
    p(f"  (b) {PENCERE_SN//60} dk pencere, ham veri     {r['state_b_ham_mb']:>14,.0f} MB"
      f"     ({r['pencere_reading']:.0f} reading/asset)")
    p(f"  (b') ayni kural, {KOVA_SN} sn kova     {r['state_b_kova_mb']:>14,.0f} MB"
      f"     ({r['kova_sayisi']:.0f} kova, sum+count)")
    p(f"  (c) {LATE_DATA_SN//3600} saat gec veri state'te  {r['state_c_gb']*1000:>14,.0f} MB"
      f"     ({r['state_c_gb']:,.0f} GB -- RAM'e sigmaz)")
    p(f"  (c) / (a) orani               {r['state_c_a_orani']:>14,.0f} x")

    p("\n-- HESAPLAMA ---------------------------------------------------")
    p(f"  ortalama                      {r['core']:>14,.2f} core   ({EVENT_ISLEME_US} us/event)")
    p(f"  tepe                          {r['tepe_core']:>14,.2f} core")

    p("\n-- INGEST POD --------------------------------------------------")
    p(f"  ortalama                      {r['pod_ort']:>14,.0f} pod    ({POD_KAPASITE_RPS:,} req/sn/pod)")
    p(f"  tepe x{TEPE}                        {r['pod_tepe']:>14,.0f} pod")
    p(f"  + N+1                         {r['pod']:>14,.0f} pod")
    p(f"  pod basina esz. baglanti      {r['pod_basina_baglanti']:>14,.0f}")

    p("\n-- COLD PATH (Faz 2, karari zorlayan sayi) ---------------------")
    p(f"  {HAM_RETENTION_GUN} gun ham satir            {r['ham_satir']:>14,.0f} satir")
    p(f"  ham boyut                     {r['ham_tb']:>14,.1f} TB")
    p(f"  sikistirilmis (/{SIKISTIRMA})            {r['sikis_tb']:>14,.1f} TB")

    p("\n-- RECOVERY BURST ----------------------------------------------")
    p(f"  senaryo: {sn(KESINTI_SN)} kesinti")
    p(f"  birikmis backlog              {r['backlog']:>14,.0f} event")
    p(f"  taban ustu fazla kapasite     {r['fazla_kapasite_eps']:>14,.0f} event/sn  (tepe-1)")
    p(f"  YAKALAMA SURESI               {sn(r['yakalama_sn']):>14}")
    p("\n  tepe faktorune gore yakalama:   yakalama = kesinti / (tepe - 1)")
    for t in (1.1, 1.5, 2, 3, 4, 6):
        y = model(tepe=t)["yakalama_sn"]
        p(f"    tepe x{t:<4}  ->  {sn(y):>10}   (ingest pod: {model(tepe=t)['pod']})")

    p("\n-- SLO BOZULMA PAYI (domain sisteme {} birakiyor) ----".format(sn(DOMAIN_BUTCE_SN)))
    for hedef, pay in (("5 sn", r["pay_5sn"]), ("60 sn", r["pay_60sn"]), ("5 dk", r["pay_300sn"])):
        durum = "KULLANILAMAZ" if pay <= 1 else ""
        p(f"  p99 <= {hedef:<6}  ->  {pay:>6.1f} x bozulma tolere edilir   {durum}")

    p("\n-- BATCH'LEME SENARYOLARI (segment karsilastirmasi) ------------")
    p("  cihaz verisini biriktirip tek istekte gonderirse:")
    for aralik, ad in ((5, "A ilac   (biriktirme yok)"), (300, "B gida   (5 dk)"), (3600, "C kuru yuk (1 saat)")):
        p(f"    {ad:<26}  {ASSET/aralik:>10,.0f} req/sn   ({ASSET/aralik/r['eps']*100:.1f}% istek yuku)")

    p("\n-- DUYARLILIK (girdiyi 2x yapinca cikti nasil degisir) ---------")
    base = model()
    ciktilar = [("kafka_tb", "Kafka TB"), ("state_a_mb", "state (a) MB"),
                ("pod", "ingest pod"), ("sikis_tb", "cold path TB"), ("core", "core")]
    girdiler = [("asset", "Asset sayisi"), ("ornekleme", "ornekleme sn"),
                ("payload", "payload B"), ("kural", "kural sayisi"), ("tepe", "tepe faktoru")]
    p(f"    {'girdi':<16}" + "".join(f"{ad:>16}" for _, ad in ciktilar))
    for key, ad in girdiler:
        yeni = model(**{key: _ikikat(key)})
        satir = f"    {ad:<16}"
        for ck, _ in ciktilar:
            o = yeni[ck] / base[ck] if base[ck] else 0
            satir += f"{o:>15.2f}x"
        p(satir)
    p("\n    (1.00x = o girdi o ciktiyi hic etkilemiyor)")
    p("=" * 68)


def _ikikat(key):
    """duyarlilik analizi icin girdinin 2 katini don"""
    d = dict(asset=ASSET, ornekleme=ORNEKLEME_SN, payload=PAYLOAD_B,
             kural=KURAL, tepe=TEPE)
    return d[key] * 2


def test():
    """bote-model.md icindeki sayilarin bu modelden ciktigini dogrula"""
    r = model()
    kontrol = [
        ("S-03 ingest hizi",        r["eps"],              20_000,     0),
        ("S-04 gunluk event",       r["gunluk_event"],     1.728e9,    0.01),
        ("C-01 degerlendirme/sn",   r["degerlendirme_eps"], 140_000,   0),
        ("2.2 bant genisligi MB/sn", r["mb_sn"],            4,         0.01),
        ("2.3 Kafka gunluk GB",     r["gunluk_gb"],        346,        0.01),
        ("2.3 Kafka disk TB",       r["kafka_tb"],         7.3,        0.05),
        ("2.3 partition event/sn",  r["partition_eps"],    417,        0.01),
        ("2.4 (a) state MB",        r["state_a_mb"],       25,         0.05),
        ("2.4 (b) ham state MB",    r["state_b_ham_mb"],   2_880,      0.05),
        ("2.4 (c) state GB",        r["state_c_gb"],       415,        0.05),
        ("2.6 core",                r["core"],             0.4,        0.01),
        ("2.7 ingest pod",          r["pod"],              9,          0),
        ("2.10 ham satir",          r["ham_satir"],        155.5e9,    0.01),
        ("2.10 sikistirilmis TB",   r["sikis_tb"],         2.1,        0.05),
        ("2.8 yakalama (24s, x2)",  r["yakalama_sn"],      86_400,     0),
        ("1.2 bozulma payi 5 sn",   r["pay_5sn"],          36,         0),
    ]
    hata = 0
    for ad, olcul, beklenen, tol in kontrol:
        ok = abs(olcul - beklenen) <= max(tol * beklenen, 1e-9)
        print(f"  [{'ok ' if ok else 'HATA'}] {ad:<26} {olcul:>14,.1f}   (beklenen ~{beklenen:,.1f})")
        hata += 0 if ok else 1
    # x4 ile yakalama kesinti/3 olmali
    assert abs(model(tepe=4)["yakalama_sn"] - KESINTI_SN / 3) < 1
    # ornekleme 2x -> state (a) degismemeli, state (b)/(c) yarilanmali
    assert abs(model(ornekleme=10)["state_a_mb"] - model()["state_a_mb"]) < 1e-6, \
        "state (a) ornekleme sikligindan BAGIMSIZ olmali"
    assert abs(model(ornekleme=10)["state_c_gb"] - model()["state_c_gb"] / 2) < 1e-6, \
        "state (c) ornekleme sikligi ile DOGRU ORANTILI olmali"
    print(f"\n  {len(kontrol)-hata}/{len(kontrol)} gecti" + ("" if not hata else f", {hata} HATA"))
    return hata


if __name__ == "__main__":
    if "--test" in sys.argv:
        sys.exit(1 if test() else 0)
    rapor()
