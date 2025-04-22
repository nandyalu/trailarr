import type {Config} from 'jest';
import presets from 'jest-preset-angular/presets';

const presetConfig = presets.createCjsPreset({});

const jestConfig: Config = {
  ...presetConfig,
  coverageDirectory: 'dist/coverage',
  collectCoverageFrom: ['src/app/**/*.ts'],
  coveragePathIgnorePatterns: ['/node_modules/', 'public-api.ts', '.module.ts', 'index.ts', '.mock.ts', 'test.ts'],
  setupFilesAfterEnv: ['<rootDir>/src/jest-setup.ts'],
  testPathIgnorePatterns: ['/node_modules/', '/dist/', '/test-util/index.ts', '.stories.ts', 'test.ts'],
  snapshotSerializers: ['jest-preset-angular/build/serializers/ng-snapshot', 'jest-preset-angular/build/serializers/html-comment'],
  reporters: ['default', 'jest-junit'],
  moduleNameMapper: {
    'src/(.*)': '<rootDir>/src/$1',
  },
};

export default jestConfig;
