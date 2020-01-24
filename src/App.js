import React, { Component } from "react";
import { Admin, Resource } from "react-admin";
import { createBrowserHistory as createHistory } from "history";
import UserIcon from "@material-ui/icons/Group";

// ENTITIES
import Dashboard from "./components/shared/Dashboard/Dashboard";
import LayoutComponent from "./components/shared/Layout";
import {
  ProjectList,
  ProjectEdit,
  ProjectCreate,
  ProjectShow
} from "./components/pages/Projects";
import {
  ExperimentList,
  ExperimentEdit,
  ExperimentCreate
} from "./components/pages/Experiments";
import { UserList } from "./components/pages/Users";

// DATA PROVIDER
import dataProvider from "./context/dataProvider";
// import fakeDataProvider from './dataProvider/FakeDataProvider';
// const dataProvider = jsonServerProvider('http://0.0.0.0:8080/projects/1');
// import { ListGuesser, EditGuesser, ShowGuesser } from 'react-admin';

// UTILS
import ExperimentIcon from "@material-ui/icons/Book";
import BusinessCenter from "@material-ui/icons/BusinessCenter";
import { activeProjectReducer } from "./context/entities/projectContext";
import ProjectContext from "./context";

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
            edit={ExperimentEdit}
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
