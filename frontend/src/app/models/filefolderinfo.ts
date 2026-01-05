import {parseDate} from './media';

export interface FileFolderInfo {
  id: number;
  media_id: number;
  parent_id: number | null;
  name: string;
  type: 'FILE' | 'FOLDER';
  size: number;
  path: string;
  is_trailer: boolean;
  modified: Date;
  children: FileFolderInfo[];
  isExpanded: boolean;
}

export function mapFileFolderInfo(info: any): FileFolderInfo {
  return {
    ...info,
    is_trailer: Boolean(info.is_trailer),
    modified: parseDate(info.modified),
    isExpanded: false,
  };
}

export function buildMediaTreeMap(files: FileFolderInfo[]): Map<number, FileFolderInfo> {
  const itemMap = new Map<number, FileFolderInfo>();
  const mediaRootMap = new Map<number, FileFolderInfo>();

  // 1. Initialize the map with node objects (one pass)
  files.forEach((file) => {
    itemMap.set(file.id, {...file, children: []});
  });

  // 2. Build relationships (one pass)
  files.forEach((file) => {
    const node = itemMap.get(file.id)!;

    if (file.parent_id === null) {
      // This is the top-level folder for this media_id
      mediaRootMap.set(file.media_id, node);
    } else {
      // Find the parent and attach as a child
      const parent = itemMap.get(file.parent_id);
      if (parent) {
        parent.children.push(node);
      }
    }
  });

  // 3. Optional: Sort children for every node (Folders first, then Name)
  mediaRootMap.forEach((root) => sortTreeRecursive(root));

  return mediaRootMap;
}

function sortTreeRecursive(node: FileFolderInfo): void {
  if (node.children.length > 0) {
    node.children.sort((a, b) => {
      // Folders first (Assuming type is 'FOLDER' or 'FILE')
      if (a.type !== b.type) {
        return a.type === 'FOLDER' ? -1 : 1;
      }
      return a.name.localeCompare(b.name);
    });
    node.children.forEach((child) => sortTreeRecursive(child));
  }
}
