/* eslint-disable prefer-rest-params */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable prefer-const */

/**
 * jest should fail on console.error logging so let's monkey-patch it to throw an actual error.
 */
let error = console.error;
console.error = function (message: any) {
  error.apply(console, arguments as any); // keep default behaviour
  throw message instanceof Error ? message : new Error(message);
};

const getMockStorage = () => {
  let storage: Record<string, string> = {};
  return {
    getItem: (key: string) => (key in storage ? storage[key] : null),
    setItem: (key: string, value: string) => (storage[key] = value || ''),
    removeItem: (key: string) => delete storage[key],
    clear: () => (storage = {}),
  };
};
Object.defineProperty(window, 'localStorage', {value: getMockStorage()});
Object.defineProperty(window, 'sessionStorage', {value: getMockStorage()});

// getComputedStyle - fake it because Angular checks in which browser it executes
Object.defineProperty(window, 'getComputedStyle', {value: () => ['-webkit-appearance']});

// deterministic now() function
Date.now = () => 1482363367071;

// deterministic random() function
Math.random = () => 0.12345;
