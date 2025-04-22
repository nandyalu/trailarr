export const msSecond = 1000;
export const msMinute = 60 * msSecond;
export const msHour = 60 * msMinute;

export function durationString(durationInMinutes: number) {
  const hours = Math.floor(durationInMinutes / 60);
  const minutes = Math.floor(durationInMinutes % 60);

  return hours === 0 ? `${minutes}m` : minutes === 0 ? `${hours}h` : `${hours}h ${minutes}m`;
}
