export type TimeseriesFrame = Record<string, unknown>;

export function frameCount(series: TimeseriesFrame[]): number {
  return series.length;
}

export function frameTime(frame: TimeseriesFrame | undefined): number {
  if (!frame) return 0;
  const t = frame.t;
  return typeof t === "number" ? t : 0;
}

export function clampFrameIndex(index: number, length: number): number {
  if (length <= 0) return 0;
  return Math.max(0, Math.min(length - 1, Math.floor(index)));
}

export function nextFrameIndex(current: number, length: number, playing: boolean, fps = 30): number {
  if (!playing || length <= 0) return clampFrameIndex(current, length);
  return clampFrameIndex(current + 1, length);
}

export function frameRobotSummary(frame: TimeseriesFrame | undefined): string {
  if (!frame) return "—";
  const entities = frame.entities as Record<string, Record<string, unknown>> | undefined;
  const robot = entities?.robot ?? entities?.target;
  const pos = robot?.position as number[] | undefined;
  if (pos && pos.length >= 3) {
    return `robot @ (${pos[0].toFixed(3)}, ${pos[1].toFixed(3)}, ${pos[2].toFixed(3)})`;
  }
  const links = frame.links as Record<string, { position?: number[] }> | undefined;
  const body = links?.body?.position;
  if (body && body.length >= 3) {
    return `body @ (${body[0].toFixed(3)}, ${body[1].toFixed(3)}, ${body[2].toFixed(3)})`;
  }
  return Object.keys(frame).join(", ");
}
