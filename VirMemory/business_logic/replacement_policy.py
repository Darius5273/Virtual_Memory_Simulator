from abc import ABC, abstractmethod


class PageReplacementPolicy(ABC):
    @abstractmethod
    def replace_page(self, pageTable, frameTable, tlb):
        """
        Replace a page in the page table, evicting an existing page if necessary.
        """
        pass

    @abstractmethod
    def access_page(self, pageIndex):
        """
        Register access to a page for replacement policy tracking.
        """
        pass


class FIFOPageReplacementPolicy(PageReplacementPolicy):
    def __init__(self):
        self.queue = []

    def access_page(self, pageIndex):
        """
        Add a page to the queue if it's not already in it.
        """
        if pageIndex not in self.queue:
            self.queue.append(pageIndex)

    def replace_page(self, pageTable, frameTable, tlb):
        """
        Evict the oldest page in the queue using FIFO logic.
        """
        if not self.queue:
            raise RuntimeError("FIFO queue is empty, no pages to replace.")

        pageIndex = self.queue.pop(0)

        tlb_invalidated_entry,frameIndex = pageTable.page_evict(pageIndex, frameTable, tlb)

        return [pageIndex, frameIndex, tlb_invalidated_entry]


class LRUPageReplacementPolicy(PageReplacementPolicy):
    def __init__(self):
        self.recentPages = []

    def access_page(self, pageIndex):
        """
        Update the page access order. Move the accessed page to the most recent position.
        """
        if pageIndex in self.recentPages:
            self.recentPages.remove(pageIndex)
        self.recentPages.append(pageIndex)

    def replace_page(self, pageTable, frameTable, tlb):
        """
        Evict the least recently used page.
        """
        if not self.recentPages:
            raise RuntimeError("LRU list is empty, no pages to replace.")

        pageIndex = self.recentPages.pop(0)

        tlb_invalidated_entry,frameIndex = pageTable.page_evict(pageIndex, frameTable, tlb)

        return [pageIndex, frameIndex, tlb_invalidated_entry]
