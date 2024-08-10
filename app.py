import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, send_file, request, redirect, url_for, session, jsonify, make_response, after_this_request
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import date, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import functools
import os
import copy
import uuid

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

app.secret_key = os.urandom(64)
app.permanent_session_lifetime = timedelta(minutes=30)  # Set session timeout

# Define the admin user
ADMIN_USER = str(os.environ.get('ADMIN_USER'))
ADMIN_PASSWORD = str(os.environ.get('ADMIN_PASSWORD'))

active_sessions = {} # Used to store sessions

# ACTUAL SHEET ITEMS *************************************************************************************************************

engine8734 = {
    "Interior: Driver Seat": [
        {"checked": False, "checked_by": "--", "item_name": "MLFD Radio (Check Battery, Check Charge)", "user_quantity": 0, "correct_quantity": 1},
    ],
    "Compartment 1: Driver Side, Transverse": [
        {"checked": False, "checked_by": "--", "item_name": "Container of Flares", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "Class A/B/C Extinguisher", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "Class D Extinguisher", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "Rolls of Caution Tape", "user_quantity": 0, "correct_quantity": 2},
        {"checked": False, "checked_by": "--", "item_name": "Slim Jim", "user_quantity": 0, "correct_quantity": 2},
        {"checked": False, "checked_by": "--", "item_name": "5\" Pony", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "Bunny Tool", "user_quantity": 0, "correct_quantity": 1}
    ],
    "Compartment 2: Driver Side, Front": [
        {"checked": False, "checked_by": "--", "item_name": "1.75\" M-M Adapter", "user_quantity": 0, "correct_quantity": 2},
        {"checked": False, "checked_by": "--", "item_name": "1.75\" F-F Adapter", "user_quantity": 0, "correct_quantity": 2},
        {"checked": False, "checked_by": "--", "item_name": "NYC-NST Adapter", "user_quantity": 0, "correct_quantity": 3},
        {"checked": False, "checked_by": "--", "item_name": "2.5\" M-M Adapter", "user_quantity": 0, "correct_quantity": 2},
        {"checked": False, "checked_by": "--", "item_name": "2.5\" F-F Adapter", "user_quantity": 0, "correct_quantity": 2},
        {"checked": False, "checked_by": "--", "item_name": "Fog Nozzle", "user_quantity": 0, "correct_quantity": 2},
        {"checked": False, "checked_by": "--", "item_name": "Smooth Bore Nozzle", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "Hose Roller", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "2.5\" Wye Gate", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "2.5\"-1.75\" Wye Gate", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "Bowring", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "45 Degree 2.5\" Adapter", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "Small Spanners (Outside)", "user_quantity": 0, "correct_quantity": 2}
    ],
    "Compartment 3: Driver Side, Mid": [
        {"checked": False, "checked_by": "--", "item_name": "Haligan", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "Flathead Axe", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "Pickheaded Axe", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "Maul", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "Whelen Portable Area Lights (Check Charge)", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "Bolt Cutter", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "Gas Shut Off Key", "user_quantity": 0, "correct_quantity": 1},
        {"checked": False, "checked_by": "--", "item_name": "Car Jack", "user_quantity": 0, "correct_quantity": 1}
    ]
}

# RANDOM IMPORTANT FUNCTIONS *****************************************************************************************************

file = open("users.txt", 'r')
userPassword = {}
for line in file:
    user = line.split(":")[0]
    pwd = line.split(":")[1]
    ini = line.split(":")[2].strip("\n")
    userPassword[user] = [pwd, ini] # {username : [password, initials]}

def right_items(engine):
    if engine == "Engine 8734":
        return engine8734
    elif engine == "Engine 8735":
        return {
    "1": [
        {"checked": False, "correct_quantity": 1, "item_name": "MLFD Radio (Check Battery, Check Charge)", "user_quantity": 0},
    ],
    "2": [
        {"checked": False, "correct_quantity": 1, "item_name": "MLFD Radio (Check Battery, Check Charge)", "user_quantity": 0},
    ] }
    elif engine == "Rescue 8730":
        return {}
    else:
        raise Exception("That Page Does Not Exist WOMPA WOMPA")

# IMPORTANT AND RANDOM ROUTES ****************************************************************************************************

@app.route('/')
def home():
    return redirect(url_for('user_dashboard'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# USER MANAGEMENT ****************************************************************************************************************

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('user'):
            return redirect(url_for('login'))

        @after_this_request
        def add_header(response):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
            return response

        return view(**kwargs)

    return wrapped_view

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if 'user' in session:
        return redirect(url_for('user_dashboard'))
    elif request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        if username == ADMIN_USER.strip() and password == ADMIN_PASSWORD.strip():
            session['user'] = ADMIN_USER
            return redirect(url_for('admin_dashboard'))
        elif username in userPassword and userPassword[username][0].strip() == password:
            session['user'] = username
            session['initials'] = userPassword[username][1]
            session['error'] = None
            # print(userPassword[username][1])
            # print(active_sessions)
            return redirect(url_for('user_dashboard'))
        else:
            error = "Login failed. Please check your credentials."
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    for item in list(active_sessions.values()):
        if session['user'] in item['users']:
            for key in list(active_sessions.keys()):
                if active_sessions[key] == item:
                    active_sessions[key]['users'].remove(session['user'])
    for room_id in list(active_sessions.keys()):
        if len(active_sessions[room_id]['users']) == 0:
            active_sessions.pop(room_id)
    session.clear()
    return redirect(url_for('login'))

# DASHBOARD **********************************************************************************************************************
    
@app.route('/user_dashboard')
@login_required
def user_dashboard():
    if session['user'] != ADMIN_USER:
        username = session['user']
        user_dir = os.path.join('user_sheets', session['user'])
        rooms = list(active_sessions.keys())
        engines = []
    
        for room_id in list(active_sessions.keys()):
            if username in active_sessions[room_id]['users']:
                active_sessions[room_id]['users'].remove(username)
        
        # for key in list(active_sessions.keys()):
            # print(f"Key: {key} | Engine: {active_sessions[key]['engine']} | Users: {active_sessions[key]['users']}")
    
        sheets = []
        if os.path.exists(user_dir):
            sheets = os.listdir(user_dir)
    
        for item in list(active_sessions.values()):
            engines.append(item['engine'])
        
        if 'error' in session:
            return render_template('user_dashboard.html', sheets=sheets, active_sessions=active_sessions, username=username, rooms=rooms, engines=engines, error=session['error'])
        else:
             return render_template('user_dashboard.html', sheets=sheets, active_sessions=active_sessions, username=username, rooms=rooms, engines=engines, error=None)
    return redirect(url_for('admin_dashboard'))

@app.route('/exit_engineering_sheet')
@login_required
def exit_engineering_sheet():
    username = session['user']

    for room_id in list(active_sessions.keys()):
        if username in active_sessions[room_id]['users']:
            active_sessions[room_id]['users'].remove(username)
        if len(active_sessions[room_id]['users']) == 0:
            active_sessions.pop(room_id)

    return redirect(url_for('user_dashboard'))

@app.route('/terminate_sheet')
@login_required
def terminate_sheet():
    username = session['user']

    for room_id in list(active_sessions.keys()):
        if username in active_sessions[room_id]['users']:
            active_sessions.pop(room_id)

    return redirect(url_for('user_dashboard'))
    
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if 'user' in session and session['user'] == ADMIN_USER:
        # List all saved engineering sheets
        sheets = []
        if os.path.exists('engineering_sheets'):
            sheets = os.listdir('engineering_sheets')
        return render_template('admin_dashboard.html', sheets=sheets)
    return redirect(url_for('login'))

# ENGINEERING SHEET MANAGEMENT ***************************************************************************************************

@app.route('/start_engineering_sheet', methods=['POST'])
@login_required
def start_engineering_sheet():
    engine = request.form.get('engine')
    if not engine:
        return redirect(url_for('user_dashboard'))
    
    engines = []
    for val in list(active_sessions.values()):
        engines.append(val['engine'])
    
    # print(engines)

    if engine in engines:    
        session['error'] = "Sorry, that engine is already being engineered. Join the sheet for that engine instead."
        return redirect(url_for("user_dashboard"))
    else:
        session_id = str(uuid.uuid4())
        session['error'] = ""
        session['room'] = session_id
        items = right_items(engine)
        session['engine'] = engine
        session['checklist_items'] = copy.deepcopy(items)
        active_sessions[session_id] = {
            'users': [session['user']],
            'engine': session['engine'],
            'owner' : session['user'],
            'checklist_items': session["checklist_items"],
            'repair_orders': {},
            'final_repair_orders': {}
        }
        session['repair_orders'] = ""
    
        return redirect(url_for('engineering_sheet', engine=engine, room_id=session_id, active_sessions=active_sessions))

@app.route('/join_engineering_sheet', methods=['POST'])
@login_required
def join_engineering_sheet():
    join_id = request.form['join_engine']
    
    if join_id in active_sessions:
        session['room'] = join_id
        session['error'] = ""
        session['checklist_items'] = active_sessions[join_id]['checklist_items']
        session['engine'] = active_sessions[join_id]['engine']
        session['repair_orders'] = active_sessions[join_id]['repair_orders'].get(session['user'], "")
        if session['user'] not in active_sessions[join_id]['users']:
            active_sessions[join_id]['users'].append(session['user'])
            # print(f"\nUsers on this sheet are: {active_sessions[join_id]['users']}\n")
        return redirect(url_for('engineering_sheet', engine=active_sessions[join_id]['engine'], room_id=join_id))
    else:
        session['error'] = "Sorry, that sheet does not exist. Create a sheet for that engine instead."
        return redirect(url_for('user_dashboard'))

@app.route('/engineering_sheet/<room_id>')
@login_required
def engineering_sheet(room_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    elif room_id not in active_sessions:
        return redirect(url_for('user_dashboard'))
    
    session['room'] = room_id
    session['error'] = ""
    session['checklist_items'] = active_sessions[room_id]['checklist_items']
    engine = active_sessions[room_id].get('engine', 'Unknown Engine')
    repair_orders = active_sessions[room_id]['repair_orders'].get(session['user'], "")
    owner_or_not = active_sessions[room_id]['owner'] == session['user']

    return render_template('index.html', active_sessions=active_sessions, engine=engine, d1=date.today().strftime("%d-%m-%Y"), checklist_items=session['checklist_items'], repair_orders=repair_orders, oon=owner_or_not)

# CHECKLIST ITEMS UPDATING *******************************************************************************************************

@app.route('/get_checklist_items')
@login_required
def get_checklist_items():
    room = session['room']
    # print(f"\nAS: {active_sessions[room]['checklist_items']}\n")
    # print(f"SS: {session['checklist_items']}\n")
    return jsonify({'checklist_items': active_sessions[room]['checklist_items']})

# CHECKBOX AND QUANTITY UPDATES **************************************************************************************************

# @app.route('/update_checkbox', methods=['POST'])
# @login_required
# def update_checkbox():
#     data = request.get_json()
#     section = data['section']
#     item_name = data['item_name']
#     checked = data['checked']

#     if section in session['checklist_items']:
#         for item in session['checklist_items'][section]:
#             if item['item_name'] == item_name:
#                 item['checked'] = checked
#                 item['checked_by'] = session['initials']
#                 session.modified = True
#                 break

#         # Update the active_sessions entry
#         if session['room'] in active_sessions:
#             active_sessions[session['room']]['checklist_items'] = session['checklist_items']

#     return jsonify({'message': 'Checkbox state updated successfully'})

@app.route('/update_checkbox', methods=['POST'])
def update_checkbox():
    data = request.get_json()
    section = data['section']
    item_name = data['item_name']
    checked = data['checked']
    checked_by = data['checked_by']

    if section in active_sessions[session['room']]['checklist_items']:
        for item in active_sessions[session['room']]['checklist_items'][section]:
            if item['item_name'] == item_name:
                if item['checked_by'] == checked_by or not item['checked']:
                    item['checked'] = checked
                    item['checked_by'] = checked_by if checked else '--'
                    print(item)
                    session.modified = True
                    break
                else:
                    return jsonify({'message': 'You cannot change this item'}), 403
                
    # Update the active_sessions entry
    if session['room'] in active_sessions:
        # active_sessions[session['room']]['checklist_items'] = session['checklist_items']
        socketio.emit('update_checklist', {'checklist_items': active_sessions[session['room']]['checklist_items']}, room=session['room'])

    return jsonify({'message': 'Checkbox updated successfully'})

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    data = request.get_json()
    section = data['section']
    item_name = data['item_name']
    new_quantity = data['new_quantity']
    checked_by = data['checked_by']

    if section in session['checklist_items']:
        for item in session['checklist_items'][section]:
            if item['item_name'] == item_name:
                if item['checked_by'] == checked_by or not item['checked']:
                    item['user_quantity'] = new_quantity
                    item['checked_by'] = checked_by if checked else '--'
                    print(item)
                    session.modified = True
                    print(item)
                    break
                else:
                    return jsonify({'message': 'You cannot change this item'}), 403
                
    print(active_sessions[session['room']]['checklist_items'][section])
    
    # Update the active_sessions entry
    if session['room'] in active_sessions:
        active_sessions[session['room']]['checklist_items'] = session['checklist_items']
        print(active_sessions[session['room']]['checklist_items'][section])
        socketio.emit('update_checklist', {'checklist_items': session['checklist_items']}, room=session['room'])
    
    return jsonify({'message': 'Quantity updated successfully'})

# @app.route('/update_quantity', methods=['POST'])
# @login_required
# def update_quantity():
#     data = request.get_json()
#     section = data['section']
#     item_name = data['item_name']
#     new_quantity = data['new_quantity']

#     if section in session['checklist_items']:
#         for item in session['checklist_items'][section]:
#             if item['item_name'] == item_name:
#                 item['user_quantity'] = new_quantity
#                 item['checked_by'] = session['initials']
#                 session.modified = True
#                 break

#         # Update the active_sessions entry
#         if session['room'] in active_sessions:
#             active_sessions[session['room']]['checklist_items'] = session['checklist_items']

#     return jsonify({'message': 'Quantity updated successfully'})

# ITEM CHANGING FROM INDEX *******************************************************************************************************
# Don't need these for now

# @app.route('/add_item', methods=['POST'])
# @login_required
# def add_item():
#     section = request.form.get('section')
#     item = request.form.get('item')
#     quantity = request.form.get('quantity')

#     if section in session['checklist_items']:
#         session['checklist_items'][section].append({
#             "checked": False,
#             "item_name": item,
#             "user_quantity": 0,
#             "correct_quantity": int(quantity)
#         })
#         session.modified = True

#     return redirect(url_for('index'))

# @app.route('/remove_item', methods=['POST'])
# @login_required
# def remove_item():
#     section = request.form.get('remove_section')
#     item_to_remove = request.form.get('item_to_remove')

#     if section in session['checklist_items']:
#         session['checklist_items'][section] = [item for item in session['checklist_items'][section] if item['item_name'] != item_to_remove]
#         session.modified = True

#     return redirect(url_for('index'))

# @app.route('/move_item', methods=['POST'])
# @login_required
# def move_item():
#     previous_category = request.form.get('previous_category')
#     item_to_move = request.form.get('item_to_move')
#     new_category = request.form.get('new_category')

#     if previous_category and new_category and item_to_move:
#         if previous_category in session['checklist_items'] and new_category in session['checklist_items']:
#             item = next((item for item in session['checklist_items'][previous_category] if item['item_name'] == item_to_move), None)
#             if item:
#                 session['checklist_items'][previous_category].remove(item)
#                 session['checklist_items'][new_category].append(item)
#                 session.modified = True

#     return redirect(url_for('index'))

# SAVING *************************************************************************************************************************

@app.route('/engineering_sheets/<filename>')
@login_required
def serve_sheet(filename):
    if 'user' in session and session['user'] == ADMIN_USER:
        return send_file(os.path.join('engineering_sheets', filename), mimetype='application/pdf')
    return redirect(url_for('login'))

@app.route('/user_sheets/<filename>')
@login_required
def serve_user_sheet(filename):
    user_dir = os.path.join('user_sheets', session['user'])
    if 'user' in session and os.path.exists(os.path.join(user_dir, filename)):
        return send_file(os.path.join(user_dir, filename), mimetype='application/pdf')
    return redirect(url_for('login'))

@app.route('/generate_pdf', methods=['POST'])
@login_required
def generate_pdf():
    data = request.get_json()
    room_id = session['room']
    repair_orders = active_sessions[session['room']]['repair_orders']
    user_repair_orders = data['repairOrders']
    repair_orders[session['user']] = user_repair_orders
    active_sessions[session['room']]['repair_orders'] = repair_orders
    checklistItems = active_sessions[session['room']]['checklist_items']
    sheetEngine = active_sessions[room_id]['engine']
    d1 = ''.join(date.today().strftime("%d-%m-%Y"))
    active_sessions[room_id]['final_repair_orders'][session['user']] = user_repair_orders

    for room_id in list(active_sessions.keys()):
        if [session['user']] == active_sessions[room_id]['users']:

            names = ''
            for guy in active_sessions[room_id]['final_repair_orders'].keys():
                names += f"{guy} "

            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
        
            # Title
            p.setFont("Helvetica-Bold", 16)
            p.drawString(100, height - 40, f"Engineering Sheet for {sheetEngine}")
        
            # Subtitles
            p.setFont("Helvetica", 12)
            p.drawString(100, height - 60, f"Engineered By: {names}")
            p.drawString(100, height - 80, f"Date: {d1}")
            
            # Checklist Items
            y = height - 120
            p.setFont("Helvetica-Bold", 14)
            p.drawString(100, y, "Checklist Items:")
            y -= 20
            p.setFont("Helvetica", 12)
            for section, items in checklistItems.items():
                p.setFont("Helvetica-Bold", 12)
                p.drawString(100, y, section + ":")
                y -= 20
                p.setFont("Helvetica", 12)
                for item in items:
                    checked_status = '√' if item['checked'] else '×'
                    p.drawString(100, y, f"{item.get('checked_by', '--')} | {checked_status} -- {item['user_quantity']}/{item['correct_quantity']} : {item['item_name']}")
                    y -= 20
                    if y < 40:  # Ensure there's enough space on the page
                        p.showPage()
                        y = height - 40
            
            # Repair Orders
            y -= 40
            p.setFont("Helvetica-Bold", 14)
            p.drawString(100, y, "Repair Orders:")
            y -= 20
            p.setFont("Helvetica", 12)
            for guy, orders in active_sessions[room_id]['final_repair_orders'].items():
                p.drawString(100, y, f"{guy}: {orders}")
                y -= 20
                if y < 40:
                    p.showPage()
                    y = height - 40
            
            p.showPage()
            p.save()

            # Save a copy for the admin
            if not os.path.exists('engineering_sheets'):
                os.makedirs('engineering_sheets')
            admin_pdf_path = os.path.join('engineering_sheets', f'{sheetEngine}_{names}_{d1}.pdf')
            with open(admin_pdf_path, 'wb') as f:
                f.write(buffer.getvalue())

            # Save a copy for the user
            for guy in active_sessions[room_id]['final_repair_orders'].keys():
                user_dir = os.path.join('user_sheets', guy)
                if not os.path.exists(user_dir):
                    os.makedirs(user_dir)
                user_pdf_path = os.path.join(user_dir, f'{sheetEngine}_{names}_{d1}.pdf')
                with open(user_pdf_path, 'wb') as f:
                    f.write(buffer.getvalue())
                
            # Close room permanently
            room = session.get('room')
            if room in active_sessions:
                socketio.emit('session_ended', room=room)

            # Remove session from active_sessions after submission
            active_sessions.pop(room)

            buffer.seek(0)  # Reset buffer to start

    # # Remove user for sheet
    # for room_id in list(active_sessions.keys()):
    #         if session['user'] in active_sessions[room_id]['users']:
    #             active_sessions[room_id]['users'].remove(session['user'])
    
    return send_file(buffer, as_attachment=True, download_name=f"Engineering_sheet_{d1}_{names}.pdf", mimetype='application/pdf')

# SOCKETIO ***********************************************************************************************************************

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'{username} has entered the room.'}, room=room)

@socketio.on('update_checklist')
def on_update_checklist(data):
    room = data['room']
    checklist_items = data['checklist_items']
    active_sessions[room]['checklist_items'] = checklist_items
    emit('update_checklist', {'checklist_items': checklist_items}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f'{username} has left the room.'}, room=room)

@socketio.on('session_ended')
def handle_session_ended():
    if 'room' in session:
        leave_room(session['room'])
        session.pop('room', None)
        session.pop('selected_engine', None)
        session.pop('checklist_items', None)
        session.pop('creator', None)
        emit('redirect', {'url': url_for('user_dashboard')})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
