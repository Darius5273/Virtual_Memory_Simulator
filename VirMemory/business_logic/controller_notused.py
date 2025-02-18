# import re
#
# from flask import Flask, jsonify, request
# app = Flask(__name__)
# class MemorySimulatorController:
#     def __init__(self, simulator):
#         self.simulator = simulator
#         self.virtual_address_width = 0
#         self.physical_memory_size = 64  # in KB
#         self.tlb_entries = 16
#         self.tlb_associativity = 0
#         self.page_table_entries = 0
#
#     def create_app(self):
#
#
#         @app.route('/reset', methods=['POST'])
#         def reset_ui():
#             """API endpoint to reset the simulation state."""
#             self.reset_ui()
#             return jsonify({'message': 'UI reset successfully'})
#
#         @app.route('/validate', methods=['POST'])
#         def validate_input():
#             """API endpoint to validate user input."""
#             data = request.json
#             try:
#                 self.virtual_address_width = int(data['virtual_address_width'])
#                 if self.virtual_address_width < 12 or self.virtual_address_width >= 25:
#                     raise ValueError("Virtual Address Width must be between 12 and 24.")
#
#                 self.physical_memory_size = int(data['physical_memory_size'])
#                 if self.physical_memory_size < 4:
#                     raise ValueError("Physical Memory Size must be at least 4 KB.")
#
#                 self.tlb_associativity = int(data['tlb_associativity'])
#                 if self.tlb_associativity <= 0 or (self.tlb_associativity & (self.tlb_associativity - 1)) != 0:
#                     raise ValueError("TLB Associativity must be a power of 2 and greater than 0.")
#
#                 self.page_table_entries = 2 ** (self.virtual_address_width - 12)
#
#             except ValueError as e:
#                 return jsonify({'error': str(e)}), 400
#
#             return jsonify({'message': 'Input validation successful'})
#
#         @app.route('/generate_system', methods=['POST'])
#         def generate_system():
#             """API endpoint to generate the system tables."""
#             if not self.validate_input():
#                 return jsonify({'error': 'Invalid input parameters'}), 400
#
#             try:
#                 self.simulator.initialize_page_table_and_tlb(
#                     virtual_address_width=self.virtual_address_width,
#                     physical_memory_size=self.physical_memory_size,
#                     page_size=4096,
#                     tlbSize=self.tlb_entries,
#                     associativity=self.tlb_associativity
#                 )
#
#                 vas = self._generate_vas_table()
#                 pt = self._generate_page_table()
#                 ram = self._generate_ram_table()
#                 tlb = self._generate_tlb_table()
#
#                 return jsonify({
#                     'virtual_address_space': vas,
#                     'page_table': pt,
#                     'ram': ram,
#                     'tlb': tlb
#                 })
#             except Exception as e:
#                 return jsonify({'error': str(e)}), 500
#
#         @app.route('/next_step', methods=['POST'])
#         def process_next_step():
#             """API endpoint for processing the next step."""
#             result = self.simulator.process_next_step()
#             return jsonify({'message': result})
#
#         @app.route('/next_address', methods=['POST'])
#         def process_next_address():
#             """API endpoint for processing the next address."""
#             result = self.simulator.process_next_address()
#             return jsonify({'message': result})
#
#         @app.route('/add_memory_address', methods=['POST'])
#         def add_memory_address():
#             """API endpoint to add a memory address."""
#             data = request.json
#             address = data.get('memory_address', '')
#             if not self._validate_memory_address(address):
#                 return jsonify({'error': 'Invalid memory address format'}), 400
#             self.simulator.add_memory_address(address)
#             return jsonify({'message': 'Memory address added successfully'})
#
#         @app.route('/default_sequence', methods=['POST'])
#         def use_default_sequence():
#             """API endpoint to use the default memory address sequence."""
#             try:
#                 with open('default_sequence.txt', 'r') as file:
#                     addresses = file.read().splitlines()
#                     self.simulator.set_memory_sequence(addresses)
#                 return jsonify({'sequence': addresses})
#             except FileNotFoundError:
#                 return jsonify({'error': 'Default sequence file not found'}), 404
#
#         @app.route('/random_sequence', methods=['POST'])
#         def generate_random_address():
#             """API endpoint to generate random memory addresses."""
#             sequence = self.simulator.generate_random_sequence()
#             self.simulator.set_memory_sequence(sequence)
#             return jsonify({'sequence': sequence})
#
#         return app
#
#     def reset_ui(self):
#         """Reset the simulation state."""
#         self.virtual_address_width = 0
#         self.physical_memory_size = 64
#         self.tlb_entries = 16
#         self.tlb_associativity = 0
#         self.page_table_entries = 0
#
#     def _generate_vas_table(self):
#         """Generate the Virtual Address Space (VAS) table."""
#         size = 2 ** self.virtual_address_width
#         return [{'virtual_address': f"0x{addr:08X}"} for addr in range(size)]
#
#     def _generate_page_table(self):
#         """Generate the Page Table."""
#         table = []
#         for i, entry in enumerate(self.simulator.pageTable.pages):
#             table.append({
#                 'index': f"0x{i:08X}",
#                 'valid': entry.validBit,
#                 'tag': f"0x{entry.address:08X}",
#                 'ppn': f"0x{entry.frame:08X}" if entry.frame >= 0 else "--"
#             })
#         return table
#
#     def _generate_ram_table(self):
#         """Generate the RAM table."""
#         size = self.physical_memory_size * 1024 // 4096
#         return [{'physical_address': f"0x{frame * 4096:08X}"} for frame in range(size)]
#
#     def _generate_tlb_table(self):
#         """Generate the TLB table."""
#         tlb = []
#         for i, entry in enumerate(self.simulator.tlb.entries):
#             tlb.append({
#                 'set': i // self.tlb_associativity,
#                 'valid': entry.valid,
#                 'tag': f"0x{entry.tag:08X}",
#                 'ppn': f"0x{entry.ppn:08X}" if entry.valid else "--"
#             })
#         return tlb
#
#     def _validate_memory_address(self, address):
#         """Validate the memory address format."""
#         required_digits = self.virtual_address_width // 4
#         pattern = rf"^0x[0-9a-fA-F]{{{required_digits}}}$"
#         return re.match(pattern, address) is not None
