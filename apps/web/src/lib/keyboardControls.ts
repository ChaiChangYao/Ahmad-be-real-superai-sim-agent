const KEY_TO_COMMAND: Record<string, string> = {
  w: "forward",
  s: "backward",
  a: "left",
  d: "right",
  " ": "jump",
  r: "reset",
  escape: "emergency_stop"
};

export function mapKeyboardToCommand(key: string): string | null {
  const lowered = key.toLowerCase();
  return KEY_TO_COMMAND[lowered] ?? null;
}

export const keyboardHelp = [
  "W/S: Forward / Backward",
  "A/D: Turn Left / Right",
  "Space: Jump",
  "R: Reset",
  "Esc: Emergency Stop"
];
