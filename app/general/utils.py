from flask import render_template, redirect, request, url_for

def render_account_template(template_name, **kwargs):
    if request.referrer and 'account' in request.referrer:
        return render_template(template_name, **kwargs)
    else:
        return redirect(url_for('user.account'))
