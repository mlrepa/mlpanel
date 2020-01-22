// Redux Action Type
export const SET_ACTIVE_PROJECT = 'CFUI/SET_ACTIVE_PROJECT';

// Redux Action
export const setActiveProject = (projectId) => ({
    type: SET_ACTIVE_PROJECT,
    payload: { projectId },
});

// Redux Reducer
export const activeProjectReducer = (previousState = 0, { type, payload }) => {
    if (type === SET_ACTIVE_PROJECT) {
        return payload.projectId;
    }
    return previousState;
}
