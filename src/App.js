import React, { Component } from "react";
import { Admin, Resource } from "react-admin";
import { createBrowserHistory as createHistory } from "history";

import Dashboard from "./components/shared/Dashboard/Dashboard";
import LayoutComponent from "./components/shared/Layout";

// Icons
import ExperimentIcon from "@material-ui/icons/Book";
import BusinessCenter from "@material-ui/icons/BusinessCenter";
import UserIcon from "@material-ui/icons/Group";

// ENTITIES
// Entities -> Experiments
import ExperimentList from "./components/pages/experiments/List";
import ExperimentShow from "./components/pages/experiments/Show";
import ExperimentCreate from "./components/pages/experiments/Create";
// Entities -> Projects
import {
  ProjectList,
  ProjectEdit,
  ProjectCreate,
  ProjectShow
} from "./components/pages/Projects";
// Entities -> Users
import { UserList } from "./components/pages/Users";

// Utils
import dataProvider from "./context/dataProvider";
import ProjectContext from "./context";
import { activeProjectReducer } from "./context/entities/projectContext";

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
          customReducers={{ activeProject: activeProjectReducer }}
        >
          <Resource
            name="projects"
            list={ProjectList}
            show={ProjectShow}
            edit={ProjectEdit}
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
          <Resource name="users" list={UserList} icon={UserIcon} />
        </Admin>
      </ProjectContext.Provider>
    );
  }
}

export default App;
