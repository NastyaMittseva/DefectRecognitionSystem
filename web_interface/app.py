import os
import datetime
import numpy as np
import hashlib
from flask import Flask
from flask import request, render_template, session, request, redirect, url_for, flash
from flask import send_from_directory, jsonify
from werkzeug.utils import secure_filename
import uuid
from flask_pymongo import PyMongo
from flask_bootstrap import Bootstrap
from flask_mongoengine import MongoEngine
from wtforms import Form
from wtforms import StringField, PasswordField
from wtforms.validators import Length, InputRequired
from werkzeug.security import check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import timedelta
from preprocessor import Preprocessor
from data_handler import DataHandler
from detection_stages import *


app = Flask(__name__)
app.config['TEMP_FOLDER'] = 'temp'
app.config['SECRET_KEY'] = 'sln7n3D}#ns!9nKL0?'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)

app.config['MONGO_URI'] = 'mongodb://localhost:27017/detection_system'
app.config['MONGODB_SETTINGS'] = {'host': 'mongodb://localhost:27017/detection_system'}

bootstrap = Bootstrap(app)
mongo = PyMongo(app)
history = mongo.db.history
users = mongo.db.users
db = MongoEngine(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Document):
    meta = {'collection': 'users'}
    name = db.StringField(max_length=30)
    password = db.StringField()


class RegForm(Form):
    name = StringField('Имя:', validators=[InputRequired(), Length(max=30)])
    password = PasswordField('Пароль:', validators=[InputRequired(), Length(min=8, max=20)])

@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()


def init_dirs_for_user(user_temp_path):
    if not os.path.exists(user_temp_path + '/imgs/'):
        os.makedirs(user_temp_path + '/imgs/')
        os.makedirs(user_temp_path + '/results_welds/')
        os.makedirs(user_temp_path + '/results_defects/')
        os.makedirs(user_temp_path + '/results_defects/welds/')
        os.makedirs(user_temp_path + '/results_defects/scale_welds/')
        os.makedirs(user_temp_path + '/results_defects/defect_mask/')
        os.makedirs(user_temp_path + '/results_defects/result/')
        os.makedirs(user_temp_path + '/results_cls_defects/')
        os.makedirs(user_temp_path + '/results_cls_defects/defect_mask/')
        os.makedirs(user_temp_path + '/results_cls_defects/results_classification/')
        os.makedirs(user_temp_path + '/results_cls_defects/results_detection/')
        os.makedirs(user_temp_path + '/results_cls_defects/scale_welds/')
        os.makedirs(user_temp_path + '/results_cls_defects/welds/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated == True:
        return redirect(url_for('start'))

    form = RegForm(request.form)
    if request.method == 'POST':
        if form.validate():
            check_user = User.objects(name=request.form['name']).first()
            if check_user and check_password_hash(check_user['password'], request.form['password']):
                session.permanent = True
                login_user(check_user)
                user_id = list(users.find({'name': current_user.name}, {}))[0]['_id']
                user_temp_path = os.path.join(app.config['TEMP_FOLDER'], str(user_id))
                init_dirs_for_user(user_temp_path)
                return redirect(url_for('start'))
            else:
                flash(u'Wrong login or password!', 'error')
                return redirect(url_for('login'))
        flash(u'Enter username and password!', 'error')
        return redirect(url_for('login'))
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
@login_required
def start():
    return render_template('start.html', name=current_user.name)


# def page_state(user_id):
#     """ Исходное состояние страницы. """
#     condition = list(history.find({'user_id': user_id}, {'created_time': 1, '_id': 0}).sort([('_id', -1)]).limit(1))
#     print(condition)
#     items = list(history.find(condition[0], {'path_to_image': 1, 'image_name': 1, 'actions': 1, '_id': False}))
#     print(items)
#     table = []
#     imgs = []
#     for i in range(len(items)):
#         actions = items[i]['actions']
#         imgs.append({'path_to_image': items[i]['path_to_image']})
#         for j in range(len(actions)):
#             row = {'id': actions[j]['id'], 'image_name': items[i]['image_name'], 'action': actions[j]['action'], 'result': actions[j]['result'], 'time': actions[j]['time']}
#             table.append(row)
#     return imgs, table


@app.route('/history', methods=['GET', 'POST'])
@login_required
def get_history():
    user_id = list(users.find({'name': current_user.name}, {}))[0]['_id']
    items = list(history.find({'user_id': user_id}))
    data = []
    for i in range(len(items)):
        actions = items[i]['actions']
        for j in range(len(actions)):
            row = {'id':actions[j]['id'], 'datatime':items[i]['created_time'],'image_name': items[i]['image_name'], 'action': actions[j]['action'], 'result': actions[j]['result'], 'time': actions[j]['time']}
            data.append(row)
    return render_template('history.html', data=data, name=current_user.name)


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'vrc'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_file_in_database(file_path, user_id, created_time, filename):
    new_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    salt_for_name = np.random.randint(1000, 10000000)
    new_filename = f'{filename}_{new_time}_{salt_for_name}'
    new_filename = hashlib.md5(new_filename.encode('utf-8')).hexdigest() + '.png'
    new_file_path = os.path.join(app.root_path, app.config['TEMP_FOLDER'], str(user_id), 'imgs', new_filename)
    os.rename(file_path, new_file_path)

    document = {'user_id': user_id, 'created_time': created_time, 'image_name': filename,
                'path_to_image': os.path.join(app.config['TEMP_FOLDER'], str(user_id), 'imgs', new_filename),
                'actions': list()}
    history.insert(document)


@app.route('/images', methods=['GET', 'POST'])
@login_required
def upload_files():
    uploaded_files = request.files.getlist("files[]")
    user_id = list(users.find({'name': current_user.name}, {}))[0]['_id']
    created_time = datetime.datetime.now().replace(microsecond=0)

    for i, uploaded_file in enumerate(uploaded_files):
        if not allowed_file(uploaded_file.filename):
            print('not allow')
            return jsonify({'message': 'Allowed file types:  png, jpg, jpeg, vrc'})

    for i, uploaded_file in enumerate(uploaded_files):
        # check Is Correct filename?
            filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(app.root_path, app.config['TEMP_FOLDER'], str(user_id), 'imgs', filename)
            uploaded_file.save(file_path)

            if filename.rsplit('.', 1)[1].lower() == 'vrc':
                data_handler = DataHandler()
                extact_folder = os.path.join(app.root_path, app.config['TEMP_FOLDER'], str(user_id), 'imgs') + '/'
                png_names = data_handler.convert_vrc_to_png(filename, extact_folder, extact_folder)
                os.remove(file_path)
                for png_name in png_names:
                    preprocessor = Preprocessor(png_name)
                    preprocessor.process_by_gradient(extact_folder)
                    preprocessor.normalize_img()
                    preprocessor.convert_to_8bit(extact_folder)
                    save_file_in_database(extact_folder + png_name, user_id, created_time, filename + '; ' + png_name)
            else:
                save_file_in_database(file_path, user_id, created_time, filename)

    condition = list(history.find({'user_id': user_id}, {'created_time':1, '_id':0}).sort([('_id', -1)]).limit(1))
    imgs = list(history.find(condition[0],{'path_to_image':1, '_id': False}))
    request_to_client = {'imgs':imgs}

    return jsonify(request_to_client)


# @app.route('/results', methods=['GET'])
# @login_required
# def get_results():
#     user_id = list(users.find({'name': current_user.name}, {}))[0]['_id']
#     _, table = page_state(user_id)
#     request_to_client = {'results': table}
#     return jsonify(request_to_client)


@app.route('/results_as_images', methods=['GET', 'POST'])
@login_required
def show_images():

    detection_results = request.form.getlist("rows[]")
    user_id = list(users.find({'name': current_user.name}, {}))[0]['_id']

    results = []
    for i in range(len(detection_results)):
        id_operation = detection_results[i].split(',')[0]
        image_name = detection_results[i].split(',')[1]
        records = list(history.find({'user_id': user_id, 'image_name':image_name},{'path_to_image':1,'actions':1, '_id': 0 }))

        path_to_image = None
        for i in range(len(records)):
            for j in range(len(records[i]['actions'])):
                if records[i]['actions'][j]['id'] == id_operation:
                    path_to_image = records[i]['path_to_image']
                    path_to_result = ''
                    if records[i]['actions'][j]['action'] == 'weld recognition':
                        path_to_result = path_to_image.replace('imgs', 'results_welds')
                    elif records[i]['actions'][j]['action'] == 'defect recognition':
                        path_to_result = os.path.join(app.config['TEMP_FOLDER'], str(user_id), 'results_defects', 'result', path_to_image.split('/')[-1])
                    elif records[i]['actions'][j]['action'] == 'defect classification':
                        path_to_result = os.path.join(app.config['TEMP_FOLDER'], str(user_id), 'results_cls_defects', 'results_classification', path_to_image.split('/')[-1])
                    break
        results.append({"path_to_image" : path_to_image, "path_to_result": path_to_result, "description":records[i]['actions'][j]['result']})

    return jsonify({'results':results})


def get_images_from_database(user_id):
    """ Получает из базы текущие изображения. """
    img_paths = []
    condition = list(history.find({'user_id': user_id}, {'created_time': 1, '_id': 0}).sort([('_id', -1)]).limit(1))
    imgs = list(history.find(condition[0], {'path_to_image': 1, '_id': False}))
    for i in range(len(imgs)):
        img_paths.append(imgs[i]['path_to_image'])
    return img_paths


@app.route('/welds', methods=['GET', 'POST'])
@login_required
def recognize_weld():
    img_paths = request.form.getlist("img_paths[]")
    user_id = list(users.find({'name': current_user.name}, {}))[0]['_id']
    if not img_paths:
        img_paths = get_images_from_database(user_id)

    request_to_client = []
    for i in range(len(img_paths)):
        action = "weld recognition"
        result, operation_time = weld_segmentation_stage(img_paths[i], img_paths[i].replace('imgs','results_welds'))
        item = list(history.find({'user_id': user_id, 'path_to_image': img_paths[i]}))[0]        
        row = {"id": str(uuid.uuid1()), "action": action, "result": result, "time": operation_time}
        history.update({'user_id': user_id, 'path_to_image': img_paths[i]}, {'$push': {'actions': row}})
        row['image_name'] = item['image_name']
#         row['created_time'] = item['created_time']
        request_to_client.append(row)
    return jsonify({'results':request_to_client})


@app.route('/defects', methods=['GET', 'POST'])
@login_required
def recognize_defects():
    img_paths = request.form.getlist("img_paths[]")
    user_id = list(users.find({'name': current_user.name}, {}))[0]['_id']
    if not img_paths:
        img_paths = get_images_from_database(user_id)

    request_to_client = []
    print(img_paths)
    for i in range(len(img_paths)):
        action = "defect recognition"

        weld_path = app.config['TEMP_FOLDER'] + '/' + str(user_id) + '/results_defects/welds/' + img_paths[i].split('/')[-1]
        path_scale_weld = weld_path.replace('welds', 'scale_welds')
        path_defect_mask = weld_path.replace('welds', 'defect_mask')
        path_results_detection = weld_path.replace('welds', 'result')
        print(img_paths[i])
        result, time = defect_segmentation_stage(img_paths[i], weld_path, path_scale_weld, path_defect_mask, path_results_detection)
        item = list(history.find({'user_id': user_id, 'path_to_image': img_paths[i]}))[0]
        row = {"id": str(uuid.uuid1()), "action": action, "result": result, "time": time}
        history.update({'user_id': user_id, 'path_to_image': img_paths[i]}, {'$push': {'actions': row}})
        row['image_name'] = item['image_name']
#         row['created_time'] = item['created_time']
        request_to_client.append(row)

    return jsonify({'results':request_to_client})


@app.route('/defects_by_class', methods=['GET', 'POST'])
@login_required
def classify_defects():

    img_paths = request.form.getlist("img_paths[]")
    user_id = list(users.find({'name': current_user.name}, {}))[0]['_id']
    if not img_paths:
        img_paths = get_images_from_database(user_id)

    request_to_client = []
    for i in range(len(img_paths)):
        action = "defect classification"

        weld_path = app.config['TEMP_FOLDER'] + '/' + str(user_id) + '/results_cls_defects/welds/' + img_paths[i].split('/')[-1]
        path_scale_weld = weld_path.replace('welds', 'scale_welds')
        path_defect_mask = weld_path.replace('welds', 'defect_mask')
        path_detection_results = weld_path.replace('welds', 'results_detection')
        path_classification_results = weld_path.replace('welds', 'results_classification')
        result, time = defect_classification_stage(img_paths[i], weld_path, path_scale_weld, path_defect_mask, path_detection_results,
                                path_classification_results)
        
        item = list(history.find({'user_id': user_id, 'path_to_image': img_paths[i]}))[0]
        row = {"id": str(uuid.uuid1()), "action": action, "result": result, "time": time}
        history.update({'user_id': user_id, 'path_to_image': img_paths[i]}, {'$push': {'actions': row}})
        row['image_name'] = item['image_name']
#         row['created_time'] = item['created_time']
        request_to_client.append(row)

    return jsonify({'results':request_to_client})


@app.route('/<path:filename>')
@login_required
def get_img(filename):
    return send_from_directory(app.root_path, filename, as_attachment=True)
