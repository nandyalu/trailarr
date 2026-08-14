import {describe, expect, it} from 'vitest';
import {fileFilterKeys, viewOnlyFilterKeys} from 'src/app/models/customfilter';
import {getFilterConditions, getFilterFieldGroups, getFilterValueType} from './form-schema';

describe('getFilterFieldGroups', () => {
  it('view filters get Media, Downloads, and Files groups', () => {
    const groups = getFilterFieldGroups('HOME');
    expect(groups.map((g) => g.label)).toEqual(['Media', 'Downloads', 'Files']);
    const downloads = groups.find((g) => g.label === 'Downloads');
    expect(downloads!.keys.sort()).toEqual([...viewOnlyFilterKeys].sort());
  });

  it('profile (TRAILER) filters do not get the Downloads group', () => {
    const groups = getFilterFieldGroups('TRAILER');
    expect(groups.map((g) => g.label)).toEqual(['Media', 'Files']);
    const offered = groups.flatMap((g) => g.keys);
    for (const key of viewOnlyFilterKeys) {
      expect(offered).not.toContain(key);
    }
  });

  it('profile (TRAILER) filters keep has_file and has_folder', () => {
    const groups = getFilterFieldGroups('TRAILER');
    const files = groups.find((g) => g.label === 'Files');
    expect(files!.keys).toEqual(fileFilterKeys);
  });

  it('no field appears in more than one group', () => {
    const offered = getFilterFieldGroups('HOME').flatMap((g) => g.keys);
    expect(new Set(offered).size).toBe(offered.length);
  });
});

describe('download_profile editor behavior', () => {
  it('offers only equals / not equals conditions', () => {
    expect(getFilterConditions('download_profile')).toEqual(['EQUALS', 'NOT_EQUALS']);
  });

  it('renders as a profile dropdown', () => {
    expect(getFilterValueType('download_profile', 'EQUALS')).toBe('profile');
  });
});
