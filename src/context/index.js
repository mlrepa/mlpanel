import React from "react";

const context = React.createContext({
  activeProjectId: null,
  activeExperimentId: null,
  activeRunId: null
});

export default context;
