export function bytesToSize(bytes: number): string {
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return '0 Byte';
  const i = parseInt(String(Math.floor(Math.log(bytes) / Math.log(1024))));
  return Math.round(bytes / Math.pow(1024, i)) + ' ' + sizes[i];
}

export function durationToTime(duration: number): string {
  const hours = Math.floor(duration / 3600);
  const minutes = Math.floor((duration % 3600) / 60);
  const seconds = duration % 60;

  let timeString = '';
  if (hours > 0) {
    timeString += hours + ':';
  }
  timeString += (minutes < 10 ? '0' : '') + minutes + ':';
  timeString += (seconds < 10 ? '0' : '') + seconds;

  return timeString;
}
