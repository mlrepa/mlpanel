import React, { Component } from "react";
import { Admin, Resource } from "react-admin";
import { createBrowserHistory as createHistory } from "history";

import Dashboard from "./components/shared/Dashboard/Dashboard";
import LayoutComponent from "./components/shared/Layout";

// Icons
import ExperimentIcon from "@material-ui/icons/Book";
import BusinessCenter from "@material-ui/icons/BusinessCenter";
import UserIcon from "@material-ui/icons/Group";
import DoubleArrowIcon from "@material-ui/icons/DoubleArrow";
import AssignmentIcon from "@material-ui/icons/Assignment";
import AddToQueueIcon from "@material-ui/icons/AddToQueue";

// ENTITIES
// Entities -> Experiments
import ExperimentList from "./components/pages/experiments/List";
import ExperimentShow from "./components/pages/experiments/Show";
import ExperimentCreate from "./components/pages/experiments/Create";
// Entities -> Projects
import ProjectList from "./components/pages/projects/List";
import ProjectCreate from "./components/pages/projects/Create";
import ProjectShow from "./components/pages/projects/Show";
// Entities -> Users
import { UserList } from "./components/pages/Users";
// Entities -> Runs
import RunList from "./components/pages/runs/List";
import RunShow from "./components/pages/runs/Show";
// Entities -> Models
import ModelList from "./components/pages/models/List";
import ModelShow from "./components/pages/models/Show";
// Entities -> Deployments
import DeploymentList from "./components/pages/deployments/List";
import DeploymentShow from "./components/pages/deployments/Show";
import DeploymentCreate from "./components/pages/deployments/Create";

// Utils
import dataProvider from "./context/dataProvider";
import ProjectContext from "./context";
import { activeProjectReducer } from "./context/entities/projectContext";
import { activeExperimentReducer } from "./context/entities/experimentContext";

const history = createHistory();

class App extends Component {
  render() {
    return (
      <ProjectContext.Provider>
        <Admin
          history={history}
          layout={LayoutComponent}
          dashboard={Dashboard}
          dataProvider={dataProvider}
          customReducers={{
            activeProject: activeProjectReducer,
            activeExperiment: activeExperimentReducer
          }}
        >
          <Resource
            name="projects"
            list={ProjectList}
            show={ProjectShow}
            create={ProjectCreate}
            icon={BusinessCenter}
          />
          <Resource
            name="experiments"
            list={ExperimentList}
            show={ExperimentShow}
            create={ExperimentCreate}
            icon={ExperimentIcon}
          />
          <Resource
            name="runs"
            list={RunList}
            show={RunShow}
            icon={DoubleArrowIcon}
          />
          <Resource
            name="registered-models"
            list={ModelList}
            show={ModelShow}
            icon={AssignmentIcon}
          />
          <Resource
            name="deployments"
            list={DeploymentList}
            show={DeploymentShow}
            create={DeploymentCreate}
            icon={AddToQueueIcon}
          />
          <Resource name="users" list={UserList} icon={UserIcon} />
        </Admin>
      </ProjectContext.Provider>
    );
  }
}

export default App;
