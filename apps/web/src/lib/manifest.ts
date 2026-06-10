export function scenarioNamesFromManifest(manifest: Record<string, unknown>): string[] {
  const scenarios = (manifest.scenarios as Array<{ name?: string }> | undefined) ?? [];
  return scenarios.map((s) => s.name ?? "Unnamed Scenario");
}
