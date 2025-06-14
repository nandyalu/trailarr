export const msSecond = 1000;
export const msMinute = 60 * msSecond;
export const msHour = 60 * msMinute;

export function durationString(durationInMinutes: number) {
  const hours = Math.floor(durationInMinutes / 60);
  const minutes = Math.floor(durationInMinutes % 60);

  return hours === 0 ? `${minutes}m` : minutes === 0 ? `${hours}h` : `${hours}h ${minutes}m`;
}

export function timeRemainingString(durationInMilliseconds: number) {
  const timeNow = Date.now();
  if (durationInMilliseconds < timeNow) {
    return '0 seconds';
  }
  durationInMilliseconds -= timeNow;
  if (durationInMilliseconds < 0) {
    return '0 seconds';
  }
  // Calculate hours, minutes, and seconds
  const hours = Math.floor(durationInMilliseconds / msHour);
  const minutes = Math.floor((durationInMilliseconds % msHour) / msMinute);
  const seconds = Math.floor((durationInMilliseconds % msMinute) / msSecond);

  if (hours === 0 && minutes === 0 && seconds === 0) {
    return '0 seconds';
  }
  if (hours === 0 && minutes === 0) {
    return `${seconds} seconds`;
  }
  if (hours === 0) {
    return `${minutes} minutes ${seconds} seconds`;
  }
  return `${hours} hours ${minutes} minutes ${seconds} seconds`;
}

export const jsonEqual = <T>(left: T, right: T): boolean => left === right || JSON.stringify(left) === JSON.stringify(right);

const cacheMap = new Map<string, any>();
export function CacheDecorator(ttl: number = 0): MethodDecorator {
  return function (target: Object, propertyKey: string | symbol, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    descriptor.value = function (...args: any[]) {
      const cacheKey = `${propertyKey.toString()}:${JSON.stringify(args)}`;
      if (cacheMap.has(cacheKey)) {
        const cachedItem = cacheMap.get(cacheKey);
        if (ttl > 0 && Date.now() - cachedItem.timestamp > ttl) {
          cacheMap.delete(cacheKey);
        } else {
          return cachedItem.value;
        }
      }
      const result = originalMethod.apply(this, args);
      cacheMap.set(cacheKey, {value: result, timestamp: Date.now()});
      return result;
    };
  };
}
