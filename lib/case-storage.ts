import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

import type { AnalysisResult, VisionOutput } from "@/lib/types";

const CASES_DIR = join(process.cwd(), "tmp", "cases");

export interface StoredCase {
  caseId: string;
  createdAt: string;
  vision: VisionOutput;
  analysis?: AnalysisResult;
}

export async function saveCase(
  caseId: string,
  vision: VisionOutput,
  analysis?: AnalysisResult,
): Promise<StoredCase> {
  await mkdir(CASES_DIR, { recursive: true });
  const record: StoredCase = {
    caseId,
    createdAt: new Date().toISOString(),
    vision,
    ...(analysis ? { analysis } : {}),
  };
  await writeFile(
    join(CASES_DIR, `${caseId}.json`),
    JSON.stringify(record, null, 2),
    "utf-8",
  );
  return record;
}

export async function loadCase(caseId: string): Promise<StoredCase | null> {
  if (!/^[a-f0-9-]{36}$/i.test(caseId)) {
    return null;
  }
  try {
    const raw = await readFile(join(CASES_DIR, `${caseId}.json`), "utf-8");
    return JSON.parse(raw) as StoredCase;
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") {
      return null;
    }
    throw err;
  }
}
