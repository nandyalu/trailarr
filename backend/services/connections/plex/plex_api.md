# PLEX API

The contents of this file have been taken from Plex API Documentation.

## Pagination

Many endpoints that return a list of items support pagination. Additionally some endpoints will force pagination and limit number of elements returned if the client attempts to request all items. To request a specific subset of data, add two headers to specify the starting offset and the number of desired items.

- **X-Plex-Container-Start** - The desired starting offset
- **X-Plex-Container-Size** - The desired number of items

Both headers should be sent in order to request paginated content. Note that it's possible to request a size of 0 on supported endpoints in order to learn the total size without actually getting any content.

The response **must** be checked to see if the response is in fact paginated. The response might not be paginated at all, or it might include a different number of items than what was requested. A paginated response will include the headers:

- **X-Plex-Container-Start** - The offset of the first returned item
- **X-Plex-Container-Total-Size** - The total size of the collection (optional but typically present)

The response body will also typically include pagination info. If the response is a `MediaContainer`, then it will have `offset` and `size` attributes representing the start index and the number of items in the current response along with an optional `totalSize` attribute for the total number of elements in the collection.

```
HTTP/1.1 200 OK
X-Plex-Container-Start: 2
X-Plex-Container-Total-Size: 5
Content-Type: application/xml

{
  "MediaContainer": {
    "size": 3,
    "totalSize": 5,
    "offset": 2,
    "Metadata" : [
      …
    ]
  }
}
```

Rather than requesting a page starting at an index, it is also possible in some lists to request a page centered on a specific item in the list.

- **X-Plex-Container-Focus-Key** - The key of an item to center on
- **X-Plex-Container-Size** - The desired number of items

The requested size is respected regardless of the position of the focus item in the list. If the item is at the start of the list and 10 items are requested, 9 items in the response will be after the item. If the item is in the middle of the list and 10 items are requested, 4 items will be before the item and 5 items will be after.

Endpoints that support rich media queries also have a `limit` parameter that interacts with pagination. Sending `limit` in a query string limits the desired number of items, much like the `X-Plex-Container-Size` header. There are two major differences:

1. When using limit, the total size of the collection is not returned. The minimum of the limit and the actual total size will be returned as the total size.
The request may be more efficient when using limit, since the total size doesn't have to be known.
2. If the total size of the collection isn't needed, use limit, since the request may be more efficient.

Note that `limit` and `X-Plex-Container-Size` aren't mutually exclusive. You can page within the results that are bounded by the limit. If you want a total of 1000 items from a collection of many thousands of items, but you want to page through them 20 at a time, you'd use `limit=1000&X-Plex-Container-Size=20&X-Plex-Container-Start=0`.


## API Versioning

PMS has never used API versioning before the creation of this document. The first published API is considered `1.0` with the API prior to publication considered `0.0`. A client species its version via the `X-Plex-Pms-Api-Version` header on requests. If no header is provided, the version `0.0` is assumed.

### API Changes

- 1.0.0 (Supported in PMS >= 1.41.9)

- Added `/downloadQueue` endpoints.

- Public release of API.

- The `includeFields` parameter has been renamed to `includeOptionalFields`. The `includeFields` parameter now means "include only these fields" where in the past it meant "please add these fields you wouldn't normally include." This was changed to be consistent with the cloud provider API.

- 1.1.0 (Supported in PMS >= 1.42.0)

    - Added ability to filter `/media/providers/metadata` endpoint by metadata types (PM-3702)
    - Changed types in `/playlists/{playlistId}/items` to array of integers.
    - Document the `/photo/:/transcode` endpoints
    - Fixed serialization of MetadataType objects for `/media/providers/metadata` calls.

- 1.1.1 (Supported in PMS >= 1.42.2)

    - Added `metadataAgentProviderGroupId` query param to create and edit library section (PM-3577)
    - Fixed Add library section method type.

- 1.2.0 (Supported in PMS >= 1.43.0)

    - Added `squareArt` as additional element type for image assets (PM-2959)
    - Added `/media/providers/metadata` endpoints (PM-1012)
    - Added delete method for `/library/metadata/{id}/{element}` (PM-4094)
    - Added documentation for Metadata-type Media Providers (PM-3051)

## Response Customization

Many endpoints allow the data that is included in the response to be tailored to exactly what the client wants. This is possible by either specifying things that should be excluded or the set of things that should be included. PMS's ability to include/exclude elements and fields is currently limited but expanding so this should be used with care.

Attributes can be customized by using a query string arg of either `excludeFields` or `includeFields`. This single parameter should be a comma-separated list of attribute names. For example, a request with `excludeFields=summary,tagline` is asking for the summary and title attributes to be left off any metadata items while the `includeFields` parameter indicated that only the specified fields should be included.

Child elements can be customized by using a query string arg of either `excludeElements` or `includeElements`. This single parameter should be a comma-separated list of element names. For example, a request with `excludeElements=Media` is asking for the Media elements to be omitted while the `includeElements` parameter indicated that only the specified elements should be included.

In addition to the above are the parameters `includeOptionalFields` and `includeOptionalElements`. These indicate that the fields/elements which are not normally included should be included in this request. One example is `includeOptionalElements=musicAnalysis` on metadata will include the `musicAnalysis` parameter which can be large and typically not needed by a client.

Trimming the response to only include what a client will actually use can result in much better performance, especially in large collections. Increasingly these are being used to select which data is fetched from the database. So if a client knows it will only ever use a few parameters from a request, it should specify those with `includeFields`.

Note that these inclusions/exclusions are treated as requests, not guarantees. Some endpoints will disregard them completely, and others may ignore them for specific items and insist on returning data that the client didn't necessarily ask for.