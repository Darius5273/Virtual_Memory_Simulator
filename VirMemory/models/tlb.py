from typing import Optional


class TLBEntry:
    def __init__(self, tag: int, physicalPageAddress: int):
        self.validBit = True
        self.tag = tag
        self.physicalPageAddress = physicalPageAddress

    def __repr__(self):
        return f"TLBEntry(tag={self.tag}, physicalPageAddress={self.physicalPageAddress}, validBit={self.validBit})"
from collections import deque

class TLB:
    def __init__(self, tlbSize: int, associativity: int):
        self.sets = {i: deque(maxlen=associativity) for i in range(tlbSize // associativity)}  # FIFO queues
        self.full_sets = {i: [None] * associativity for i in range(tlbSize // associativity)}  # Fixed slots
        self.associativity = associativity
        self.tlbHits = 0
        self.tlbMisses = 0
        self.tlbSize = tlbSize

    def check_and_add_entry(self, vpn: int, ppn: int) -> int:
        """
        Add or replace an entry in the appropriate TLB set using FIFO.
        Returns the exact index of the newly added entry in the TLB.
        """
        set_index = vpn % len(self.sets)
        entry = TLBEntry(tag=vpn, physicalPageAddress=ppn)

        if len(self.sets[set_index]) >= self.associativity:
            evicted_entry = self.sets[set_index].popleft()
            self.full_sets[set_index][self.full_sets[set_index].index(evicted_entry)] = None

        self.sets[set_index].append(entry)
        entry_index = -1
        for i in range(self.associativity):
            if self.full_sets[set_index][i] is None:
                self.full_sets[set_index][i] = entry
                entry_index = i
                break

        return set_index * self.associativity + entry_index  # Global index in TLB

    def lookup(self, vpn: int):
        """
        Perform a TLB lookup.
        Returns a dictionary with the entry and its exact global index in the TLB.
        """
        set_index = vpn % len(self.sets)
        for i, entry in enumerate(self.full_sets[set_index]):
            if entry and entry.tag == vpn and entry.validBit:
                self.tlbHits += 1
                global_index = set_index * self.associativity + i
                return [entry, global_index]

        self.tlbMisses += 1
        return [None,-1]

    def invalidate_entry(self, tag: int):
        """Invalidate an entry corresponding to the given tag."""
        for set_index, entries in self.full_sets.items():
            for i, entry in enumerate(entries):
                if entry and entry.tag == tag:
                    self.full_sets[set_index][i].validBit = False
                    self.sets[set_index] = deque(
                        [e for e in self.sets[set_index] if e.tag != tag],
                        maxlen=self.associativity
                    )
                    return set_index * self.associativity + i
