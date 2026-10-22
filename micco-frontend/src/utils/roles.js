const PRIVILEGED_ROLES = ['Admin', 'Trưởng phòng', 'Giám đốc', 'Phó giám đốc'];

export function isPrivilegedRole(role) {
    return PRIVILEGED_ROLES.includes(role);
}

export function isAdminRole(role) {
    return role === 'Admin';
}
