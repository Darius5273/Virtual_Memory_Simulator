from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import re
from business_logic.simulator import Simulator

app = Flask(__name__)
CORS(app)

simulator = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate_system", methods=["POST"])
def generate_system():
    global simulator
    data = request.json

    try:
        required_fields = ["virtual_address_width", "tlb_associativity", "page_replacement_policy"]
        missing_fields = [field for field in required_fields if field not in data or data[field] == ""]
        if missing_fields:
            return jsonify({"error": f"Missing input: {', '.join(missing_fields)}"}), 400

        try:
            virtual_address_width = int(data["virtual_address_width"])
        except ValueError:
            return jsonify({"error": "Virtual Address Width must be an integer."}), 400

        try:
            tlb_associativity = int(data["tlb_associativity"])
        except ValueError:
            return jsonify({"error": "TLB Associativity must be an integer."}), 400
        page_replacement_policy = data["page_replacement_policy"]

        if virtual_address_width < 12 or virtual_address_width > 25:
            return jsonify({"error": "Virtual Address Width must be between 12 and 25 bits."}), 400
        if tlb_associativity <= 0 or not (tlb_associativity & (tlb_associativity - 1)) == 0 or tlb_associativity >16:
            return jsonify({"error": "TLB Associativity must be a positive integer smaller than 16 and a power of 2."}), 400

        simulator = Simulator(
            policy=page_replacement_policy,
            vas=virtual_address_width,
            associativity=tlb_associativity
        )
        vas_table = simulator.generate_vas_table()
        pt_table = simulator.generate_page_table()
        ram_table = simulator.generate_ram_table()
        tlb_table = simulator.generate_tlb_table()

        return jsonify({
            "message": "System successfully generated.",
            "tables": {
                "vas": vas_table,
                "page_table": pt_table,
                "ram": ram_table,
                "tlb": tlb_table
            }
        })

    except TypeError as e:
        return jsonify({"error": f"Missing input."}), 400
    except ValueError:
        return jsonify({"error": "Invalid input format."}), 400

@app.route("/reset_system", methods=["POST"])
def reset_system():
    """API endpoint to reset the system."""
    global simulator
    simulator = None
    return jsonify({
        "message": "System reset successfully."
    })

@app.route("/upload_address_sequence", methods=["POST"])
def upload_address_sequence():
    global simulator
    if not simulator:
        return jsonify({"error": "Simulator not initialized. Generate the system first."}), 400

    try:
        for _ in range(10):
            simulator.generate_random_address()

        formatted_sequence = simulator.display_address_sequence()
        return jsonify({
            "message": "Address sequence uploaded successfully.",
            "sequence": formatted_sequence
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/add_address", methods=["POST"])
def add_address():
    global simulator
    if not simulator:
        return jsonify({"error": "Simulator not initialized. Please generate the system first."}), 400

    data = request.json
    try:
        address = data["address"]
        if not validate_memory_address(address):
            return jsonify({"error": "Invalid address."}), 400
        simulator.add_memory_address(address)
        formatted_sequence = simulator.display_address_sequence()
        return jsonify({"sequence": formatted_sequence})
    except KeyError:
        return jsonify({"error": "Missing address in request."}), 400

@app.route("/generate_random_address", methods=["POST"])
def generate_random_address():
    global simulator
    if simulator is None:
        return jsonify({"error": "Simulator not initialized. Please generate the system first."}), 400

    simulator.generate_random_address()
    formatted_sequence = simulator.display_address_sequence()
    return jsonify({"sequence": formatted_sequence})

@app.route("/next_step", methods=["POST"])
def next_step():
    global simulator
    if simulator is None:
        return jsonify({"error": "Simulator not initialized. Please generate the system first."}), 400

    messages = simulator.process_next_step()
    stats = get_statistics()
    formatted_sequence = simulator.display_address_sequence()
    pt_table = simulator.generate_page_table()
    tlb_table = simulator.generate_tlb_table()

    response = {"messages": messages, "stats": stats, "sequence": formatted_sequence, "colors": simulator.color_state,
                "page_table": pt_table,"tlb_table": tlb_table}
    print(response)
    return jsonify(response), 200

@app.route("/next_address", methods=["POST"])
def next_address():
    global simulator
    if not simulator:
        return jsonify({"error": "Simulator not initialized. Please generate the system first."}), 400

    messages = simulator.process_next_address()
    stats = get_statistics()
    formatted_sequence = simulator.display_address_sequence()
    pt_table = simulator.generate_page_table()
    tlb_table = simulator.generate_tlb_table()

    return jsonify({"messages": messages, "stats": stats,"sequence": formatted_sequence, "colors": simulator.color_state,
                    "page_table": pt_table,"tlb_table": tlb_table})

def get_statistics():
    global simulator
    if not simulator:
        return jsonify({"error": "Simulator not initialized."}), 400

    simulator.calculate_hit_rates()

    stats = {
        "tlb_hits": simulator.tlbHit,
        "tlb_misses": simulator.tlbMiss,
        "tlb_hit_rate": simulator.tlbHitRate,
        "pt_hits": simulator.ptHit,
        "pt_misses": simulator.ptMiss,
        "pt_hit_rate": simulator.ptHitRate,
    }
    return stats

def validate_memory_address(address):
        if int(address,16) < 2 ** simulator.vasWidth:
            return True
