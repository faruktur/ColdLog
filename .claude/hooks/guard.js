// PreToolUse guard: (1) commit agent tarafından atılmaz, (2) Kabul durumundaki ADR değiştirilmez.
// Kurallar: .claude/rules/core.md — kural 4 ve kural 11.
const fs = require("fs");

const deny = (reason) => {
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: reason,
      },
    })
  );
  process.exit(0);
};

let raw = "";
process.stdin.on("data", (c) => (raw += c));
process.stdin.on("end", () => {
  let d = {};
  try {
    d = JSON.parse(raw || "{}");
  } catch {
    process.exit(0); // girdi okunamadıysa engellemeyiz
  }
  const tool = d.tool_name || "";
  const input = d.tool_input || {};

  // 1 — commit / push / tag / reset: kullanıcının denetiminde atılır
  if (tool === "Bash" || tool === "PowerShell") {
    const cmd = String(input.command || "");
    if (/\bgit\b[\s\S]*?\b(commit|push|tag|reset|revert)\b/.test(cmd)) {
      deny(
        "core.md kural 11: commit/push agent tarafından atılmaz. Ne commit edilmesi gerektiğini ve mesaj taslağını yaz, komutu kullanıcı kendisi çalıştırsın."
      );
    }
    return process.exit(0);
  }

  // 2 — Durumu *Kabul* olan ADR dosyası değiştirilemez
  const p = String(input.file_path || "").replace(/\\/g, "/");
  if (!/\/docs\/05-adr\/\d{4}-[^/]*\.md$/.test(p)) return process.exit(0);

  let durum = "";
  try {
    durum = (fs.readFileSync(p, "utf8").match(/^\|\s*\*\*Durum\*\*\s*\|.*$/m) || [""])[0];
  } catch {
    return process.exit(0); // yeni ADR dosyası
  }
  if (/Kabul/.test(durum) && !/Öneri|Kabul\*?\s*değil/.test(durum)) {
    deny(
      `core.md kural 4: ${p.split("/").pop()} durumu *Kabul*; ADR silinmez ve içeriği değiştirilmez. Karar değişiyorsa kullanıcıya sor — doğru yol yeni bir ADR yazıp bunun durumunu *Değiştirildi* yapmak, bunu da kullanıcı onaylar.`
    );
  }
  process.exit(0);
});

// shortcut: Bash üzerinden (sed/heredoc) yapılan ADR değişikliği yakalanmaz, sadece Edit/Write yakalanır.
// Gerekirse Bash komut metninde 05-adr yolu aranarak genişletilir.
