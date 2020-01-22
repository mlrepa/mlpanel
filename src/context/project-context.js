import React from 'react';

const projectContext = React.createContext({
    activeProject: null,
    activate: () => {}
});

export default projectContext;