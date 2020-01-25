import React from "react";

const context = React.createContext({
  activeProjectId: null,
  activeExperimentId: null
});

export default context;
