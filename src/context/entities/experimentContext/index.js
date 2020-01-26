// Redux Action Type
export const SET_ACTIVE_EXPERIMENT = "APP/SET_ACTIVE_EXPERIMENT";

// Redux Action
export const setActiveExperiment = experimentId => ({
  type: SET_ACTIVE_EXPERIMENT,
  payload: { experimentId }
});

// Redux Reducer
export const activeExperimentReducer = (state = 0, { type, payload }) => {
  if (type === SET_ACTIVE_EXPERIMENT) {
    return payload.experimentId;
  }
  return state;
};
