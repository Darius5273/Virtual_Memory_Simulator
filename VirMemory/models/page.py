

class Page:
    def __init__(self, index: int):
        self.validBit = False
        self.frame = -1
        self.index = index

    def __repr__(self):
        return f"validBit={self.validBit}, frame={self.frame}, index={self.index})"

class PageTable:
    def __init__(self, numPages: int, pageSize: int):
        self.numPages = numPages
        self.pages = [Page(index=i) for i in range(numPages)]
        self.pageFaults = 0
        self.pageSize = pageSize

    def get_available_frame(self, frameTable):
        """Return the first free frame, or -1 if none are available."""
        for i in range(len(frameTable)):
            if not frameTable[i]:
                return i
        return -1

    def page_evict(self, pageIndex, frameTable, tlb):
        """Evict a page and update the frame table and TLB."""
        page = self.pages[pageIndex]
        frameIndex = page.frame
        if frameIndex != -1:
            frameTable[frameIndex] = False
        page.validBit = False
        tlb_invalid_entry = tlb.invalidate_entry(pageIndex)
        return [tlb_invalid_entry,frameIndex]

    def access_page(self, pageIndex, frameTable, tlb, replacementPolicy):
        """Access a page, updating page table, TLB, and frame table."""
        page = self.pages[pageIndex]
        if page.validBit:
            return page.frame
        else:
            self.pageFaults += 1
            freeFrame = self.get_available_frame(frameTable)

            if freeFrame == -1:
                replacementPolicy.replace_page(self, frameTable, tlb)

            page.validBit = True
            frameTable[freeFrame] = True
            page.frame = freeFrame
            return freeFrame
