import type {
  FullConfig,
  Reporter,
  Suite,
  TestCase,
  TestResult,
} from "@playwright/test/reporter";
import * as fs from "fs";
import * as path from "path";

export default class JsonlReporter implements Reporter {
  private readonly outputPath: string;
  private readonly companyId: string;

  constructor() {
    const data = new Date().toISOString().slice(0, 10);
    const repoRoot = path.resolve(__dirname, "../../../");
    const dir = path.join(repoRoot, "reports", data);
    fs.mkdirSync(dir, { recursive: true });
    this.outputPath = path.join(dir, "falhas.jsonl");
    this.companyId = process.env.QA_COMPANY_ID ?? "";
  }

  onBegin(_config: FullConfig, _suite: Suite): void {}

  onTestEnd(test: TestCase, result: TestResult): void {
    if (result.status === "passed" || result.status === "skipped") return;

    const erros = result.errors.map(e => e.message ?? String(e)).join(" | ");
    const erro  = erros || result.status;
    const caminho = test.titlePath().filter(Boolean);
    const modulo  = caminho.slice(1, -1).join(" > ") || "desconhecido";

    const entrada: Record<string, string> = {
      timestamp:    new Date().toISOString().replace("T", " ").slice(0, 19),
      modulo,
      cenario:      test.title,
      erro,
      fase:         "execucao",
    };
    if (this.companyId) entrada.company_id_usado = this.companyId;

    fs.appendFileSync(this.outputPath, JSON.stringify(entrada) + "\n", "utf-8");
  }

  printsToStdio(): boolean { return false; }
}
