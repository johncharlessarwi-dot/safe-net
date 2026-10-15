"""Tenant scoping helpers.

Every page works on the current tenant: the logged-in admin's tenant, or for a
platform super-admin, the tenant they switched into (session['tenant_id']).
Always fetch owned rows through scoped()/owned_or_404() so one tenant can never
read or change another tenant's data.
"""
from functools import wraps

from flask import abort, flash, redirect, session, url_for
from flask_login import current_user
from sqlalchemy import select, union

from i18n import tr
from models import db, Tenant, RadUser, Voucher, Site


def current_tenant():
    if not current_user.is_authenticated:
        return None
    if current_user.is_superadmin and session.get('tenant_id'):
        tenant = db.session.get(Tenant, session['tenant_id'])
        if tenant:
            return tenant
    return current_user.tenant


def tenant_id():
    tenant = current_tenant()
    if not tenant:
        abort(403)
    return tenant.id


def tenant_sites(tid=None):
    """The tenant's sites, oldest (the main site) first; creates one if there are none."""
    tid = tid if tid is not None else tenant_id()
    sites = Site.query.filter_by(tenant_id=tid).order_by(Site.id).all()
    if not sites:
        site = Site(tenant_id=tid, name='Main site')
        db.session.add(site)
        db.session.commit()
        sites = [site]
    return sites


def current_site():
    """The site picked in the top bar, or None for all sites."""
    if not current_user.is_authenticated:
        return None
    fixed = getattr(current_user, 'site_id', None)
    if fixed and not current_user.is_superadmin:             # a partner limited to one site
        site = db.session.get(Site, fixed)
        return site if site and site.tenant_id == tenant_id() else None
    sid = session.get('site_id')
    if not sid:
        return None
    site = db.session.get(Site, sid)
    return site if site and site.tenant_id == tenant_id() else None


def site_for_new_things():
    """New devices and vouchers go to the picked site, or the main site."""
    return current_site() or tenant_sites()[0]


def scoped(model):
    """model.query limited to the current tenant."""
    return model.query.filter(model.tenant_id == tenant_id())


def owned_or_404(model, obj_id):
    obj = scoped(model).filter(model.id == obj_id).first()
    if obj is None:
        abort(404)
    return obj


def tenant_usernames(tid=None):
    """SELECT of every RADIUS username (users + voucher codes) owned by a tenant,
    for filtering radacct / radpostauth, which have no tenant column."""
    tid = tid if tid is not None else tenant_id()
    return union(select(RadUser.username).where(RadUser.tenant_id == tid),
                 select(Voucher.code).where(Voucher.tenant_id == tid))


def role_required(role):
    """Allow only admins with at least `role` (staff < admin < owner)."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if not current_user.has_role(role):
                flash(tr("You don't have permission to open that page."), 'warning')
                return redirect(url_for('dashboard'))
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def superadmin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_superadmin:
            abort(404)
        return fn(*args, **kwargs)
    return wrapper
