

from pyGoogleImages.searcher import GoogleImageSearch

async def main():
    async with GoogleImageSearch(safe_search=True) as search:
        results = await search.search("cute cats", page=0)
        for img in results:
            print(img.url, img.safe_search)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())