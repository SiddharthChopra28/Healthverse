import {makeCharts} from './graphs.js'

function getAge(dateString) {
    var today = new Date();
    var birthDate = new Date(dateString);
    var age = today.getFullYear() - birthDate.getFullYear();
    var m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    return age;
}


function refreshDate() {
    const dateElem = document.getElementById('date');

    var date = new Date();

    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

    var presentable_date = monthNames[date.getMonth()] + ' ' + date.getDate() + ', ' + date.getFullYear();

    dateElem.innerHTML = presentable_date;


}

function refreshName() {
    const name = document.getElementById('name');
    const age = document.getElementById('age');
    const gender = document.getElementById('gender');

    var uname = localStorage.getItem('username');
    var dob = localStorage.getItem('dob');
    var ugender = localStorage.getItem('gender');

    var uage = getAge(dob)

    if (!(uname == 'null')) {
        name.innerHTML = uname.substring(0, 9) + '...'
        age.innerHTML = uage
        gender.innerHTML = ugender
    }
    else {
        name.innerHTML = 'Guest'
    }
}

function regUser(list) {
    if (!(text == 'False')) {
        localStorage.setItem('username', list[0]);
        localStorage.setItem('dob', list[1]);
        localStorage.setItem('gender', list[2]);

        const loginElem = document.getElementById('login');
        const mainElem = document.getElementById('main');
        loginElem.hidden = true;
        mainElem.hidden = false;
        refreshName();
    }
    else {
        const message = document.getElementById('message')
        message.innerHTML = "Incorrect email or password. Please visit <a href=\"https://site.healthverse.repl.co/\" target=\"_blank\">the site for further action.</a>";
    }

}

function changeUser() {
    const hello = document.getElementById('hello');
    hello.innerHTML = 'Welcome,';

    const name = document.getElementById('name');
    name.innerHTML = 'Guest';

    const login = document.getElementById('login');
    login.hidden = false;

    const main = document.getElementById('main');
    main.hidden = true;

}

function init_auth() {
    text = this.responseText;
    list = text.split(',')
    regUser(list)
}

function auth() {
    var email = document.getElementById('email');
    var pwd = document.getElementById('pwd');


    let str = "https://site.healthverse.repl.co/api-auth?email=" + email.value + '&pwd=' + pwd.value;

    try {
        var request = new XMLHttpRequest();
        request.onload = init_auth;
        request.open("GET", str);
        request.send(null);

    }
    catch (error) {
        const new_message = document.getElementById('message');
        new_message.innerHTML = 'Sorry, there was some trouble in logging you in.';

    }
    event.preventDefault();

}

function store_data() {
    var json = this.responseText;
    var username = localStorage.getItem('username')
    var object = JSON.parse(json)
    var user_object = object[username]

    var cts = JSON.stringify(user_object['ct'])
    var evals = JSON.stringify(user_object['eval'])
    var xrays = JSON.stringify(user_object['xray'])

    console.log(evals)

    localStorage.setItem('cts', cts)
    localStorage.setItem('evals', evals)
    localStorage.setItem('xrays', xrays)

    makeReports();

} 

function makeIntFromTime(str){
    if(str==null){
        return 0
    }

    var first = str.split(' ');
    var sec = first[0].split('-');
    var third = first[1].split(':');
    var fourth = third[third.length - 1].split('.');

    var date = sec.join('');
    var mins = third.slice(0, third.length-1);
    var time = mins[0]+mins[1]+fourth[0]+fourth[1]

    var totalTime = date+time
    return parseInt(totalTime)
}


function makeReports() {
    const latrep = document.getElementById('latrep');
    const lattest = document.getElementById('lattest');
    const lattype = document.getElementById('lattype');

    var cts = JSON.parse(localStorage.getItem('cts'));
    var evals = JSON.parse(localStorage.getItem('evals'));
    var xrays = JSON.parse(localStorage.getItem('xrays'));
    
    var cts_keys = Object.keys(cts);
    var evals_keys = Object.keys(evals)
    var xrays_keys = Object.keys(xrays)

    var max_dates = [cts_keys[cts_keys.length - 1], evals_keys[evals_keys.length -1], xrays_keys[xrays_keys.length -1]]
    var int_max_dates = max_dates.map(makeIntFromTime)


    if (int_max_dates[0]>int_max_dates[1] && int_max_dates[0]>int_max_dates[2]){
        var latest_test = 0
        var latest_type = 'CT Scan Evaluation'
        var latest_obj = cts
    }
    else if (int_max_dates[1]>int_max_dates[0] && int_max_dates[1]>int_max_dates[2]){
        var latest_test = 1
        var latest_type = 'Self-evaluation Test'
        var latest_obj = evals
    }
    else if (int_max_dates[2]>int_max_dates[0] && int_max_dates[2]>int_max_dates[1]){
        var latest_test = 2
        var latest_type = 'X-Ray Scan Evaluation'
        var latest_obj = xrays
    }

    lattest.innerHTML = max_dates[latest_test].split('.')[0];
    lattype.innerHTML = latest_type;
    latrep.innerHTML = (parseFloat(latest_obj[max_dates[latest_test]]) > 0.5) ? 'Positive' : 'Negative'
    
    var ct_vals = Object.values(cts).map(parseFloat)
    var eval_vals = Object.values(evals).map(parseFloat)
    var xray_vals = Object.values(xrays).map(parseFloat)
    
    makeCharts(ct_vals, eval_vals, xray_vals);

}

document.getElementById('form').addEventListener('submit', auth);

document.getElementById('change').addEventListener('click', changeUser);

var username = localStorage.getItem('username')
console.log(username)
if (username == 'null') {
    refreshDate();
    refreshName();
    changeUser();
}

else {
    refreshDate();
    refreshName();

    var request = new XMLHttpRequest();
    request.onload = store_data;
    var user = localStorage.getItem('username')
    var url = "https://site.healthverse.repl.co/api-get?uname=" + user;
    request.open("GET", url);
    request.send(null);

}