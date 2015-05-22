from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from datetime import date
import requests
# local modules
import auth2 as d2lauth
import appconfig
from forms import RequestForm

# MOVE APP ID AND KEY INTO SEPARATE CONFIG FILE
appContext = d2lauth.fashion_app_context(app_id=appconfig.APP_ID,#'PkThAwhB0a3Xg6R2SjVugg',
                                         app_key=appconfig.APP_KEY)

# constants for calculating semester code
BASE_YEAR = 1945
FALL = '0'
SPRING = '5'
SUMMER = '8'

JAN = 1
MAY = 5
AUG = 8
DEC = 12


@view_config(route_name='logout')
def logout(request):
    '''
    Dumps session data
    '''
    request.session.invalidate()
    return HTTPFound(location=appconfig.REDIRECT_AFTER_LOGOUT)

#@view_config(route_name='login', renderer='templates/login.pt')
@view_config(route_name='login', renderer='templates/login.jinja2')
def login(request):
    auth_url = appContext.create_url_for_authentication(
            host=appconfig.LMS_HOST, 
            client_app_url=appconfig.AUTH_CB,
            encrypt_request=appconfig.ENCRYPT_REQUESTS)
    #try:
    #    request.session['error']
    #except KeyError:
    #    request.session['error'] = []
    print request.scheme # CHECKING FOR HTTPS
    return {'auth_url': auth_url}

'''
@view_config(route_name='auth', renderer='templates/test.pt')
def auth(request):
    # beta uc
    
    uc = appContext.create_user_context(
        result_uri=request.url, 
        host='uwosh-beta.courses.wisconsin.edu',
        encrypt_requests=True)

    r = requests.get(uc.create_authenticated_url(
        '/d2l/api/lp/1.4/users/whoami'))
    request.session['first_name'] = r.json()['FirstName']
    return {}


@view_config(route_name='session_check', renderer='templates/session_check.pt')
def session_check(request):
    first_name = request.session['first_name']
    return {'first_name': first_name}
'''

#@view_config(route_name='request', renderer='templates/request.pt')
@view_config(route_name='request', renderer='templates/request.jinja2')
def request_form(request):

    session = request.session
    if 'url_for_uc' not in session:
        session['url_for_uc'] = request.url
    print session

    uc = appContext.create_user_context(
        result_uri=session['url_for_uc'], 
        host=appconfig.LMS_HOST,
        encrypt_requests=appconfig.ENCRYPT_REQUESTS)

    user_data = get_user_data(uc)
    store_user_data(session, user_data)
    code = get_semester_code()

    session['course_list'] = get_courses(uc, code)
    form = RequestForm(request.POST)
    form.course.choices = get_course_choices(session['course_list'])

    print request.scheme #CHECKING FOR HTTPS

    if request.method == 'POST' and form.validate():
        embed = 'no'
        if form.embed.data:
            embed = 'yes'
        download = 'no'
        if form.download.data:
            download = 'yes'
        share = 'no'
        if form.share.data:
            share = 'yes'
        training = 'no'
        if form.training.data:
            training = 'yes'
            
        session['requestDetails'] = {
            'courseId' : str(form.course.data),
            'embed' : embed,
            'download' : download,
            'share' : share,
            'training' : training,
            'location' : form.location.data,
            'courseName' : form.courseName.data,
            'comments' : form.comments.data,
            'expiration' : form.expiration.data
            }

        return HTTPFound(location=request.route_url('confirmation'))
    else:
        return {'form': form}


#@view_config(route_name='confirmation', renderer='templates/confirmation.pt')
@view_config(route_name='confirmation', renderer='templates/confirmation.jinja2')
def confirmation_page(request):
    form = RequestForm()
    session = request.session
    print request.scheme #CHECKING FOR HTTPS
    return {
        'name': session['firstName'] + " " + session['lastName'],
        'form': form,
        'requestDetails': session['requestDetails']
        }

###########
# helpers #
###########

def get_user_data(uc):
    '''
    Requests current user info from D2L via whoami route
    http://docs.valence.desire2learn.com/res/user.html#get--d2l-api-lp-%28version%29-users-whoami
    '''
    my_url = uc.create_authenticated_url(
        '/d2l/api/lp/{0}/users/whoami'.format(appconfig.VER))
    return requests.get(my_url).json()


def store_user_data(session, userData):
    '''
    Stores user info in session.
    '''
    session['firstName'] = userData['FirstName']
    session['lastName'] = userData['LastName']
    session['userId'] = userData['Identifier']
    '''PRODUCTION: UNCOMMENT FOLLOWING LINE AND DELETE THE ONE AFTER THAT'''
    #session['uniqueName'] = userData['UniqueName']
    session['uniqueName'] = 'lookerb'


def get_semester_code():
    '''
    Computers current semester code by today's date.
    '''
    year = date.today().year - BASE_YEAR
    month = date.today().month
    if month >= 8 and month <= 12:
        semester = FALL
    elif month >= 1 and month <= 5:
        semester = SPRING
        year = year - 1
    else: # month is between
        semester = SUMMER
        year = year - 1
    code = str(year) + semester
    while len(code) < 4:
        code = '0' + code
    # DELETE FOLLOWING LINE FOR PRODUCTION
    code = '0685'
    return code


def get_courses(uc, semester_code):
    '''
    Creates dictionary of lists of courses keyed by semester code and stores
    it in session for easy access post-creation.
    '''
    my_url = uc.create_authenticated_url(
        '/d2l/api/lp/{0}/enrollments/myenrollments/'.format(appconfig.VER))
    kwargs = {'params': {}}
    kwargs['params'].update({'orgUnitTypeId': appconfig.ORG_UNIT_TYPE_ID})
    r = requests.get(my_url, **kwargs)
    course_list = []
    end = False
    while end == False:
        for course in r.json()['Items']:
            sem_code = str(course['OrgUnit']['Code'][6:10])
            if sem_code == semester_code:
                course_list.append({u'courseId': int(course['OrgUnit']['Id']),
                    u'name': course['OrgUnit']['Name'],
                    u'code': course['OrgUnit']['Code'],
                    u'parsed': parse_code(course['OrgUnit']['Code'])})
            if r.json()['PagingInfo']['HasMoreItems'] == True:
                kwargs['params']['bookmark'] = r.json()['PagingInfo']['Bookmark']
                r = requests.get(my_url, **kwargs)
            else:
                end = True
    return course_list


def get_course_choices(course_list):
    link_prefix = "<a target=\"_blank\" href='http://" +\
        appconfig.LMS_HOST + \
        "/d2l/home/"
    choices = [(course['courseId'],
        course['name'] +
        ", " +
        course['parsed'] +
        link_prefix + 
        str(course['courseId']) +
        "'> D2L Page</a>") for course in course_list]
    return choices


def parse_code(code):
    '''
    Breaks up code into more readable version to present to user.
    '''
    parsed = code.split("_")
    return parsed[3] + " " + parsed[4] + " " + parsed[5]

