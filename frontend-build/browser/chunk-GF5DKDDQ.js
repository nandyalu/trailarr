// src/util.ts
var msSecond = 1e3;
var msMinute = 60 * msSecond;
var msHour = 60 * msMinute;
function durationString(durationInMinutes) {
  const hours = Math.floor(durationInMinutes / 60);
  const minutes = Math.floor(durationInMinutes % 60);
  return hours === 0 ? `${minutes}m` : minutes === 0 ? `${hours}h` : `${hours}h ${minutes}m`;
}
var jsonEqual = (left, right) => left === right || JSON.stringify(left) === JSON.stringify(right);

export {
  msMinute,
  durationString,
  jsonEqual
};
//# sourceMappingURL=chunk-GF5DKDDQ.js.map
