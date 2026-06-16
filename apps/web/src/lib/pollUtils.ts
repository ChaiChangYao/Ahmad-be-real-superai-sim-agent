/** Poll errors that should retry while a long Genesis showcase run is in progress. */
export function isTransientPollError(message: string): boolean {
  return (
    message.includes("timed out") ||
    message.includes("Cannot reach API") ||
    message.includes("Failed to fetch") ||
    message.includes("NetworkError") ||
    message.includes("Load failed")
  );
}
