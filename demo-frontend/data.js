/* ========================================================================
   Records Management System — Data Layer (localStorage-backed JSON store)
   Seeds initial data on first load, provides CRUD APIs for all entities.
   ======================================================================== */

const DataStore = (() => {
  const STORAGE_KEY = 'rms_data';

  // ── Seed Data ──────────────────────────────────────────────────────────

  const SEED = {
    users: [
      { id: 'u001', username: 'admin',  password: 'admin123',  firstName: 'John',  lastName: 'Doe',    email: 'john.doe@company.com',    phone: '+1 (555) 123-4567', department: 'Engineering', jobTitle: 'Senior QA Engineer', bio: 'Experienced QA engineer specializing in test automation and quality assurance processes.', role: 'Admin',    status: 'Active', lastActive: 'Just now' },
      { id: 'u002', username: 'sarah',  password: 'sarah123',  firstName: 'Sarah', lastName: 'Connor', email: 'sarah.connor@company.com', phone: '+1 (555) 234-5678', department: 'Compliance',  jobTitle: 'Compliance Officer',  bio: '', role: 'Reviewer', status: 'Active', lastActive: '5 min ago' },
      { id: 'u003', username: 'mike',   password: 'mike123',   firstName: 'Mike',  lastName: 'Chen',   email: 'mike.chen@company.com',    phone: '+1 (555) 345-6789', department: 'Infrastructure', jobTitle: 'DevOps Engineer', bio: '', role: 'Editor',   status: 'Active', lastActive: '1 hour ago' },
      { id: 'u004', username: 'emily',  password: 'emily123',  firstName: 'Emily', lastName: 'Park',   email: 'emily.park@company.com',   phone: '+1 (555) 456-7890', department: 'HR',             jobTitle: 'HR Specialist',  bio: '', role: 'Editor',   status: 'Active', lastActive: '2 hours ago' },
      { id: 'u005', username: 'alex',   password: 'alex123',   firstName: 'Alex',  lastName: 'Kim',    email: 'alex.kim@company.com',     phone: '+1 (555) 567-8901', department: 'Legal',          jobTitle: 'Legal Analyst',  bio: '', role: 'Viewer',   status: 'Inactive', lastActive: '3 days ago' },
      { id: 'u006', username: 'lisa',   password: 'lisa123',   firstName: 'Lisa',  lastName: 'Wong',   email: 'lisa.wong@company.com',    phone: '+1 (555) 678-9012', department: 'Compliance',  jobTitle: 'Senior Auditor', bio: '', role: 'Reviewer', status: 'Active', lastActive: '30 min ago' }
    ],

    records: [
      { id: 'r001', title: 'Q4 Financial Review',    type: 'Compliance',      status: 'Draft',          assigneeId: 'u002', priority: 'High',     dueDate: '2026-03-15', description: 'Comprehensive financial review for Q4 2025 covering revenue analysis, expense tracking, budget variance reports, and compliance documentation for regulatory filing. All department heads must submit their quarterly reports by March 1, 2026.', attachments: ['Q4_Revenue_Report.xlsx', 'Budget_Variance.pdf', 'Compliance_Checklist.docx'], createdBy: 'u001', createdAt: '2026-02-25T09:30:00', updatedAt: '2026-02-28T15:15:00' },
      { id: 'r002', title: 'Server Migration Plan',  type: 'Infrastructure',  status: 'Approved',       assigneeId: 'u003', priority: 'Medium',   dueDate: '2026-03-22', description: 'Plan for migrating on-premise servers to cloud infrastructure. Includes timeline, risk assessment, and rollback procedures.', attachments: ['Migration_Timeline.pdf'], createdBy: 'u003', createdAt: '2026-02-20T10:00:00', updatedAt: '2026-02-28T13:42:00' },
      { id: 'r003', title: 'Employee Onboarding SOP', type: 'HR Document',    status: 'Draft',          assigneeId: 'u004', priority: 'Low',      dueDate: '2026-04-01', description: 'Standard operating procedure for employee onboarding including document checklist, orientation schedule, and IT setup requirements.', attachments: [], createdBy: 'u004', createdAt: '2026-02-22T14:00:00', updatedAt: '2026-02-27T17:30:00' },
      { id: 'r004', title: 'Data Retention Policy',  type: 'Policy',          status: 'Locked',         assigneeId: 'u001', priority: 'Critical', dueDate: '2026-02-28', description: 'Company-wide data retention policy covering data classification, retention periods, disposal methods, and regulatory compliance requirements.', attachments: ['Retention_Schedule.xlsx', 'Legal_Requirements.pdf'], createdBy: 'u001', createdAt: '2026-01-15T09:00:00', updatedAt: '2026-02-27T11:08:00' },
      { id: 'r005', title: 'Vendor Risk Assessment',  type: 'Compliance',     status: 'Rejected',       assigneeId: 'u005', priority: 'Medium',   dueDate: '2026-03-10', description: 'Risk assessment of third-party vendors covering data security practices, business continuity, and compliance certifications.', attachments: ['Vendor_Survey_Results.xlsx'], createdBy: 'u005', createdAt: '2026-02-10T11:00:00', updatedAt: '2026-02-26T16:55:00' },
      { id: 'r006', title: 'Annual Security Audit',  type: 'Compliance',      status: 'Approved',       assigneeId: 'u006', priority: 'High',     dueDate: '2026-03-05', description: 'Annual security audit covering network security, access controls, incident response procedures, and vulnerability assessments.', attachments: ['Audit_Report_2025.pdf', 'Findings_Summary.docx'], createdBy: 'u006', createdAt: '2026-02-05T08:30:00', updatedAt: '2026-02-28T10:20:00' }
    ],

    notifications: [
      { id: 'n001', text: 'Record #1042 was approved by Sarah Connor', time: '2 minutes ago',  read: false, userId: 'u001', recordId: 'r001' },
      { id: 'n002', text: 'New record assigned to you: "Q4 Compliance Audit"', time: '15 minutes ago', read: false, userId: 'u001', recordId: null },
      { id: 'n003', text: 'Record #1038 was rejected — review comments added', time: '1 hour ago', read: false, userId: 'u001', recordId: 'r005' },
      { id: 'n004', text: 'Monthly report "Feb 2026" is ready to export', time: '3 hours ago', read: true, userId: 'u001', recordId: null }
    ],

    activityLog: [
      { id: 'a001', recordId: 'r001', userId: 'u001', action: 'created this record',              timestamp: '2026-02-25T09:30:00' },
      { id: 'a002', recordId: 'r001', userId: 'u001', action: 'updated the description',           timestamp: '2026-02-25T10:15:00' },
      { id: 'a003', recordId: 'r001', userId: 'u001', action: 'attached 3 files',                  timestamp: '2026-02-26T14:00:00' },
      { id: 'a004', recordId: 'r001', userId: 'u001', action: 'assigned to Sarah Connor',          timestamp: '2026-02-27T08:45:00' },
      { id: 'a005', recordId: 'r002', userId: 'u003', action: 'created this record',              timestamp: '2026-02-20T10:00:00' },
      { id: 'a006', recordId: 'r002', userId: 'u003', action: 'submitted for review',             timestamp: '2026-02-22T09:00:00' },
      { id: 'a007', recordId: 'r002', userId: 'u002', action: 'approved this record',             timestamp: '2026-02-25T14:30:00' },
      { id: 'a008', recordId: 'r004', userId: 'u001', action: 'created this record',              timestamp: '2026-01-15T09:00:00' },
      { id: 'a009', recordId: 'r004', userId: 'u001', action: 'locked this record',               timestamp: '2026-02-27T11:08:00' }
    ],

    nextIds: { record: 7, notification: 5, activity: 10, user: 7 }
  };

  // ── Internal Helpers ───────────────────────────────────────────────────

  let _data = null;

  function _load() {
    if (_data) return _data;
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try { _data = JSON.parse(raw); return _data; } catch (e) { /* corrupt, re-seed */ }
    }
    _data = JSON.parse(JSON.stringify(SEED));
    _save();
    return _data;
  }

  function _save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(_data));
  }

  function _genId(type) {
    const d = _load();
    const num = d.nextIds[type]++;
    _save();
    const prefix = { record: 'r', notification: 'n', activity: 'a', user: 'u' }[type];
    return prefix + String(num).padStart(3, '0');
  }

  function _getUserName(userId) {
    const d = _load();
    const u = d.users.find(u => u.id === userId);
    return u ? `${u.firstName} ${u.lastName}` : 'Unknown';
  }

  function _addActivity(recordId, userId, action) {
    const d = _load();
    d.activityLog.push({
      id: _genId('activity'),
      recordId,
      userId,
      action,
      timestamp: new Date().toISOString()
    });
    _save();
  }

  // ── Public API ─────────────────────────────────────────────────────────

  return {
    init() { _load(); },

    resetToSeed() {
      _data = JSON.parse(JSON.stringify(SEED));
      _save();
    },

    // ── Session ──────────────────────────────────────────────────────────
    getCurrentUser() {
      const userId = sessionStorage.getItem('rms_current_user');
      if (!userId) return null;
      const d = _load();
      return d.users.find(u => u.id === userId) || null;
    },

    setCurrentUser(userId) {
      sessionStorage.setItem('rms_current_user', userId);
    },

    logout() {
      sessionStorage.removeItem('rms_current_user');
    },

    authenticateUser(username, password) {
      const d = _load();
      const user = d.users.find(u => u.username === username && u.password === password && u.status === 'Active');
      return user || null;
    },

    // ── Users ────────────────────────────────────────────────────────────
    getUsers() {
      return _load().users.slice();
    },

    getUserById(id) {
      return _load().users.find(u => u.id === id) || null;
    },

    inviteUser(email, role) {
      const d = _load();
      const namePart = email.split('@')[0];
      const firstName = namePart.split('.')[0] || namePart;
      const lastName = namePart.split('.')[1] || '';
      const user = {
        id: _genId('user'),
        username: namePart,
        password: namePart + '123',
        firstName: firstName.charAt(0).toUpperCase() + firstName.slice(1),
        lastName: lastName.charAt(0).toUpperCase() + lastName.slice(1),
        email,
        phone: '',
        department: '',
        jobTitle: '',
        bio: '',
        role,
        status: 'Active',
        lastActive: 'Never'
      };
      d.users.push(user);
      _save();
      return user;
    },

    deactivateUser(id) {
      const d = _load();
      const user = d.users.find(u => u.id === id);
      if (user) { user.status = 'Inactive'; _save(); }
      return user;
    },

    reactivateUser(id) {
      const d = _load();
      const user = d.users.find(u => u.id === id);
      if (user) { user.status = 'Active'; _save(); }
      return user;
    },

    // ── Records ──────────────────────────────────────────────────────────
    getRecords(filters = {}) {
      const d = _load();
      let recs = d.records.slice();

      if (filters.status)   recs = recs.filter(r => r.status.toLowerCase() === filters.status.toLowerCase());
      if (filters.type)     recs = recs.filter(r => r.type.toLowerCase() === filters.type.toLowerCase());
      if (filters.search) {
        const s = filters.search.toLowerCase();
        recs = recs.filter(r => r.title.toLowerCase().includes(s) || r.description.toLowerCase().includes(s));
      }
      if (filters.dateFrom) recs = recs.filter(r => r.updatedAt >= filters.dateFrom);
      if (filters.dateTo)   recs = recs.filter(r => r.updatedAt <= filters.dateTo + 'T23:59:59');
      if (filters.showArchived === false) recs = recs.filter(r => r.status !== 'Archived');

      if (filters.sortBy) {
        const key = filters.sortBy;
        const dir = filters.sortDir === 'desc' ? -1 : 1;
        recs.sort((a, b) => {
          let va = a[key] || '', vb = b[key] || '';
          if (key === 'assignee') {
            va = _getUserName(a.assigneeId);
            vb = _getUserName(b.assigneeId);
          }
          return va < vb ? -dir : va > vb ? dir : 0;
        });
      } else {
        recs.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
      }

      return recs;
    },

    getRecordById(id) {
      return _load().records.find(r => r.id === id) || null;
    },

    createRecord(data) {
      const d = _load();
      const currentUser = this.getCurrentUser();
      const record = {
        id: _genId('record'),
        title: data.title,
        type: data.type,
        status: 'Draft',
        assigneeId: data.assigneeId || (currentUser ? currentUser.id : 'u001'),
        priority: data.priority || 'Medium',
        dueDate: data.dueDate || '',
        description: data.description || '',
        attachments: data.attachments || [],
        createdBy: currentUser ? currentUser.id : 'u001',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      d.records.push(record);
      _save();
      _addActivity(record.id, record.createdBy, 'created this record');
      return record;
    },

    updateRecord(id, data) {
      const d = _load();
      const rec = d.records.find(r => r.id === id);
      if (!rec) return null;
      Object.assign(rec, data, { updatedAt: new Date().toISOString() });
      _save();
      const currentUser = this.getCurrentUser();
      _addActivity(id, currentUser ? currentUser.id : 'u001', 'updated this record');
      return rec;
    },

    deleteRecord(id) {
      const d = _load();
      const idx = d.records.findIndex(r => r.id === id);
      if (idx === -1) return false;
      d.records.splice(idx, 1);
      _save();
      return true;
    },

    updateRecordStatus(id, newStatus, comment) {
      const d = _load();
      const rec = d.records.find(r => r.id === id);
      if (!rec) return null;
      rec.status = newStatus;
      rec.updatedAt = new Date().toISOString();
      _save();
      const currentUser = this.getCurrentUser();
      const userId = currentUser ? currentUser.id : 'u001';
      const actionMap = {
        'Pending Review': 'submitted for review',
        'Approved': 'approved this record',
        'Rejected': 'rejected this record',
        'Locked': 'locked this record',
        'Archived': 'archived this record',
        'Draft': 'unlocked this record'
      };
      let action = actionMap[newStatus] || `changed status to ${newStatus}`;
      if (comment) action += ` — "${comment}"`;
      _addActivity(id, userId, action);
      return rec;
    },

    // ── Dashboard ────────────────────────────────────────────────────────
    getDashboardStats() {
      const recs = _load().records;
      const total = recs.length;
      const approved = recs.filter(r => r.status === 'Approved').length;
      const pending = recs.filter(r => r.status === 'Pending Review').length;
      const locked = recs.filter(r => r.status === 'Locked').length;
      const draft = recs.filter(r => r.status === 'Draft').length;
      const rejected = recs.filter(r => r.status === 'Rejected').length;
      const archived = recs.filter(r => r.status === 'Archived').length;
      return { total, approved, pending, locked, draft, rejected, archived };
    },

    // ── Notifications ────────────────────────────────────────────────────
    getNotifications(userId) {
      const d = _load();
      return d.notifications.filter(n => !userId || n.userId === userId);
    },

    getUnreadCount(userId) {
      return this.getNotifications(userId).filter(n => !n.read).length;
    },

    markAllNotificationsRead(userId) {
      const d = _load();
      d.notifications.forEach(n => {
        if (!userId || n.userId === userId) n.read = true;
      });
      _save();
    },

    // ── Activity Log ─────────────────────────────────────────────────────
    getActivityLog(recordId) {
      const d = _load();
      return d.activityLog
        .filter(a => a.recordId === recordId)
        .sort((a, b) => a.timestamp.localeCompare(b.timestamp));
    },

    // ── Profile / Settings ───────────────────────────────────────────────
    saveProfile(data) {
      const d = _load();
      const currentUser = this.getCurrentUser();
      if (!currentUser) return null;
      const user = d.users.find(u => u.id === currentUser.id);
      if (!user) return null;
      if (data.firstName !== undefined) user.firstName = data.firstName;
      if (data.lastName !== undefined)  user.lastName  = data.lastName;
      if (data.email !== undefined)     user.email     = data.email;
      if (data.phone !== undefined)     user.phone     = data.phone;
      if (data.department !== undefined) user.department = data.department;
      if (data.jobTitle !== undefined)  user.jobTitle  = data.jobTitle;
      if (data.bio !== undefined)       user.bio       = data.bio;
      _save();
      return user;
    },

    changePassword(currentPassword, newPassword) {
      const d = _load();
      const currentUser = this.getCurrentUser();
      if (!currentUser) return { success: false, error: 'Not logged in' };
      const user = d.users.find(u => u.id === currentUser.id);
      if (!user) return { success: false, error: 'User not found' };
      if (user.password !== currentPassword) return { success: false, error: 'Current password is incorrect' };
      user.password = newPassword;
      _save();
      return { success: true };
    },

    // ── Helpers ──────────────────────────────────────────────────────────
    getUserName(userId) { return _getUserName(userId); },

    getAssigneeName(assigneeId) { return _getUserName(assigneeId); },

    formatDate(isoString) {
      if (!isoString) return '—';
      const d = new Date(isoString);
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    },

    formatDateTime(isoString) {
      if (!isoString) return '—';
      const d = new Date(isoString);
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) + ' • ' +
             d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
    },

    formatDateFull(isoString) {
      if (!isoString) return '—';
      const d = new Date(isoString);
      return d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    }
  };
})();

// Auto-initialize on load
DataStore.init();
