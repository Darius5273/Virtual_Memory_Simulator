import math
import random
import re

from business_logic.replacement_policy import FIFOPageReplacementPolicy, LRUPageReplacementPolicy
from models.page import PageTable
from models.tlb import TLBEntry, TLB


class Simulator:
    def __init__(self,policy, vas,associativity):
        self.pageTable = None
        self.tlb = None
        print(policy)
        self.set_page_replacement_policy(policy)
        self.vasSize = 0
        self.vasWidth = 0
        self.pageSize = 4096
        self.memorySize = 64
        self.addressSequence = []
        self.numPages = 0
        self.case = 0
        self.ppn1 = None

        self.tlbHit = 0
        self.tlbMiss = 0
        self.tlbHitRate = 0.0
        self.ptHit = 0
        self.ptMiss = 0
        self.ptHitRate = 0.0

        self.currentStep = 0
        self.currentAddressIndex = 0
        self.messages = []
        self.initialize_page_table_and_tlb(vas,self.pageSize,associativity)

        self.color_changes = {"vas": [], "pt": [], "tlb": [], "ram": []}
        self.color_state = {
            "vas": {}, "pt": {}, "tlb": {}, "ram": {}
        }
        self.frameTable = [False for i in range(self.memorySize // 4)]

    def initialize_page_table_and_tlb(self, virtual_address_width, page_size, associativity):

        self.numPages = 2 ** (virtual_address_width - 12)
        num_frames = 64 // page_size

        self.pageTable=PageTable(self.numPages, num_frames)
        self.tlb=TLB(16,associativity)
        self.vasSize = 2**virtual_address_width
        self.vasWidth = virtual_address_width

    def add_memory_address(self, addr):
        addr_long = int(addr, 16)
        self.addressSequence.append(addr_long)

    def set_memory_sequence(self, addresses):
        self.addressSequence = [int(addr, 16)  for addr in addresses]

    def set_page_replacement_policy(self, policy):
        """Set the page replacement policy (FIFO or LRU)."""
        if policy == "FIFO":
            self.pageReplacementPolicy = FIFOPageReplacementPolicy()
        else:
            self.pageReplacementPolicy = LRUPageReplacementPolicy()
        print(self.pageReplacementPolicy)

    def calculate_hit_rates(self):
        """Update hit rates for TLB and Page Table."""
        totalTlbAccesses = self.tlbHit + self.tlbMiss
        self.tlbHitRate = (self.tlbHit / totalTlbAccesses) * 100 if totalTlbAccesses > 0 else 0.0

        totalPtAccesses = self.ptHit + self.ptMiss
        self.ptHitRate = (self.ptHit / totalPtAccesses) * 100 if totalPtAccesses > 0 else 0.0

    def reset_steps(self):
        """Reset the simulator's step counter."""
        self.currentStep = 0
        self.messages = []

    def update_color(self, table_type, index, color):
        """Update the color for an entry and track the changes."""
        if self.color_state[table_type].get(index) != color:
            self.color_changes[table_type].append({"index": index, "color": color})
            self.color_state[table_type][index] = color

    def reset_colors(self):
        """Reset colors for entries that were previously marked."""
        for table_type, changes in self.color_changes.items():
            for change in changes:
                current_color = change["color"]
                index = change["index"]
                if current_color == "red" or current_color == "gray":
                    self.update_color(table_type, index, "white")
                elif current_color == "green":
                    self.update_color(table_type, index, "DodgerBlue")

    def break_virtual_address(self, virtualAddress):
        """Break the virtual address into VPN and PO."""
        vpn = virtualAddress // self.pageSize
        po = virtualAddress % self.pageSize
        return vpn, po

    def tlb_lookup(self, vpn):
        """Perform a TLB lookup and return the result."""
        tlbIndex = vpn % len(self.tlb.sets)
        tag = vpn


        # Generate messages for TLB lookup
        self.messages.append(f"Breaking VPN into TLB Index and tag")
        self.messages.append(f"TLB Set: 0x{tlbIndex:X}, tag: 0x{tag:X}")
        self.messages.append(f"Checking set: 0x{tlbIndex:X}")
        self.messages.append(f"Checking if set contains an entry with tag: 0x{tag:X}")

        entry, index = self.tlb.lookup(tag)

        if entry:
            self.tlbHit += 1
            self.messages.append(f"(Checking if discovered entry is valid)")
            self.messages.append(f"TLB hit")
            self.messages.append(f"PPN: 0x{entry.physicalPageAddress:X}")
            self.update_color("tlb", index, "green")
            self.update_color("ram", entry.physicalPageAddress, "green")
            self.currentStep=3
            self.pageReplacementPolicy.access_page(vpn)
            return entry.physicalPageAddress
        else:
            self.tlbMiss += 1
            for i in range(self.tlb.associativity):
                self.update_color("tlb", tlbIndex*self.tlb.associativity+i, "red")
            self.messages.append(f"TLB miss")
            self.currentStep += 1
            return None

    def page_table_lookup(self, vpn):
        """Check the page table for a VPN and return the result."""
        page = self.pageTable.pages[vpn]
        self.messages.append(f"Checking page table...")
        self.messages.append(f"Checking if VPN: 0x{vpn:X} has valid entry")

        if page.validBit:
            self.ptHit += 1
            self.pageReplacementPolicy.access_page(page.index)
            self.update_color("pt", vpn, "green")
            self.messages.append(f"Page Table entry valid")
            self.messages.append(f"Page Table hit")
            return page.frame
        else:
            self.ptMiss += 1
            self.update_color("pt", vpn, "red")
            self.messages.append(f"Page Table entry invalid")
            self.messages.append(f"Page Table miss")
            return None

    def update_tlb(self, vpn, ppn):
        """Update the TLB using the FIFO replacement policy."""
        self.messages.append(f"Update TLB with new PTE found using First In First Out replacement policy")
        global_index = self.tlb.check_and_add_entry(vpn, ppn)
        self.update_color("tlb", global_index, "green")


    def handle_page_fault(self, vpn):
        """Handle a page fault by loading the page from secondary memory."""

        freeFrame = self.pageTable.get_available_frame(self.frameTable)
        if freeFrame == -1:
            if isinstance(self.pageReplacementPolicy, FIFOPageReplacementPolicy):
                policy = "FIFO"
            else:
                policy = "LRU"
            evictedPageIndex,frameIndex,tlb_invalidated = self.pageReplacementPolicy.replace_page(self.pageTable, self.frameTable, self.tlb)
            self.messages.append(f"Evicted page index: 0x:{evictedPageIndex:X}")
            self.update_color("pt", evictedPageIndex, "gray")
            self.update_color("ram", frameIndex, "gray")
            if tlb_invalidated!=None:
                self.update_color("tlb", tlb_invalidated, "gray")
            self.currentStep -= 1
            self.messages.append(f"Update Page Table with PPN using {policy} replacement policy")
            self.messages.append(f"Evicted page index: 0x{evictedPageIndex:X}")
            return
        self.pageTable.pages[vpn].frame = freeFrame
        self.pageTable.pages[vpn].validBit = True
        self.frameTable[freeFrame] = True
        self.pageReplacementPolicy.access_page(vpn)
        self.update_color("ram", freeFrame, "green")
        self.update_color("pt", vpn, "green")

        self.update_tlb(vpn, freeFrame)

    def process_next_step(self):
        """Process the next step of the simulation."""
        va = math.ceil(math.log2(self.vasSize))
        pa = math.ceil(math.log2(self.memorySize))
        if self.currentAddressIndex >= len(self.addressSequence):
            return "Simulation Complete"

        virtualAddress = self.addressSequence[self.currentAddressIndex]
        vpn, po = self.break_virtual_address(virtualAddress)
        self.reset_colors()
        if self.currentStep!=0: self.messages.append("-----")

        if self.currentStep == 0:
            self.case = 0
            self.ppn1 = None
            self.messages=[]
            self.messages.append(f"Break down virtual address into VPN, PO(page offset)")
            self.messages.append(f"VPN: 0x{vpn:X}, PO: 0x{po:X}")
            self.update_color("vas", vpn, "pink")
            self.tlb_lookup(vpn)

        elif self.currentStep == 1:
            ppn = self.page_table_lookup(vpn)
            if ppn is not None:
                self.case = 1
                self.ppn1 = ppn
            else:
                self.messages.append(f"Page requested is not found in Page Table")
                self.messages.append(f"Data will be loaded from Secondary Memory")
                self.case = 0
            self.currentStep += 1

        elif self.currentStep == 2:
            if self.case == 1:
                self.update_tlb(vpn, self.ppn1)
                self.messages.append(f"PPN: 0x{self.ppn1:X}")
            else:
                self.handle_page_fault(vpn)

            self.currentStep += 1
        elif self.currentStep == 3:
            self.update_color("vas", vpn, "DodgerBlue")
            self.messages.append(f"Done!")
            self.currentAddressIndex += 1
            self.currentStep = 0

        return "\n".join(self.messages)

    def process_next_address(self):
        """Process the current address completely."""
        if self.currentStep ==0:
            self.process_next_step()
        while self.currentStep:
            self.process_next_step()
        return "\n".join(self.messages)

    def generate_random_address(self):
        """Generate a sequence of virtual addresses."""
        address_width = self.vasWidth
        max_address = 2 ** address_width - 1
        address = random.randint(0, max_address)
        self.addressSequence.append(address)

    def generate_vas_table(self):
            """Generate the Virtual Address Space (VAS) table."""
            size = 2 ** self.vasWidth
            required_digits = (self.vasWidth -12)//4
            if required_digits > 1:
                return [{'virtual_address': f"0x{addr:0{required_digits}X}"} for addr in range(size // self.pageSize)]
            else :
                return [{'virtual_address': f"0x{addr:X}"} for addr in range(size // self.pageSize)]

    def generate_page_table(self):
        """Generate the Page Table."""
        table = []
        size = self.memorySize * 1024 // 4096
        required_digits = (math.ceil(math.log2(size)))//4
        for i, entry in enumerate(self.pageTable.pages):
            if required_digits == 1: table.append({
                'index': f"0x{entry.index:X}",
                'valid': entry.validBit,
                'ppn': f"0x{entry.frame:X}" if entry.frame >= 0 else "--"
            })
            else:
                table.append({
                    'index': f"0x{entry.index:X}",
                    'valid': entry.validBit,
                    'ppn': f"0x{entry.frame:X}" if entry.frame >= 0 else "--"
                })
        return table

    def generate_ram_table(self):
        """Generate the RAM table."""
        size = self.memorySize * 1024 // 4096
        return [{'physical_address': f"0x{frame:X}"} for frame in range(size)]

    def generate_tlb_table(self):
        """Generate the TLB table with all indexes and dynamic formatting."""
        tlb_table = []

        vas_width = self.vasWidth
        ph_mem_size = self.memorySize

        for set_index, entries in self.tlb.full_sets.items():
            for i, entry in enumerate(entries):
                if entry is not None:
                    tlb_table.append({
                        'set': set_index,
                        'valid': entry.validBit,
                        'tag': f"0x{entry.tag:X}",
                        'ppn': f"0x{entry.physicalPageAddress:X}"
                    })
                else:
                    tlb_table.append({
                        'set': set_index,
                        'valid': 0,
                        'tag': "--",
                        'ppn': "--"
                    })
        return tlb_table

    def formatted_string(self,width,value):
        hex_length = len(f"{value:X}")
        if hex_length < width:
            formatted_string = f"{value:0{width}X}"
        else:
            formatted_string = f"{value:X}"
        return formatted_string


    def display_address_sequence(self):
        required_digits = math.ceil(self.vasWidth // 4)
        hex_addr = [f"0x{addr:0{required_digits}X}" for addr in self.addressSequence]
        formatted_sequence = [
            f"> {hex_addr[self.currentAddressIndex]}" if i == self.currentAddressIndex else hex_addr[i]
            for i in range(len(hex_addr))
        ]
        return formatted_sequence