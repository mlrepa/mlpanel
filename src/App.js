import React, { Component } from 'react';
import { Admin, Resource } from 'react-admin';

// ENTITIES
import Dashboard from './Dashboard/Dashboard';
import AppLayout from './Layout/AppLayout';
import { ProjectList, ProjectEdit, ProjectCreate, ProjectShow } from './Projects/Projects';
import { ExperimentList, ExperimentEdit, ExperimentCreate } from './Experiments/Experiments'
import { UserList } from './Users';
import UserIcon from '@material-ui/icons/Group';

// DATA PROVIDER
import dataProvider from './DataProvider/DataProvider';
// import fakeDataProvider from './DataProvider/FakeDataProvider';
// const dataProvider = jsonServerProvider('http://0.0.0.0:8080/projects/1');
// import { ListGuesser, EditGuesser, ShowGuesser } from 'react-admin';

// UTILS 
import ExperimentIcon from '@material-ui/icons/Book';
import BusinessCenter from '@material-ui/icons/BusinessCenter';
import { activeProjectReducer } from './activeProjectContext/activeProjectContext';
import ProjectContext from './context/project-context'


class App extends Component {

  render() {
    return (
      <ProjectContext.Provider>
        <Admin 
          layout={AppLayout} 
          dashboard={Dashboard} 
          dataProvider={dataProvider}
          customReducers={{ activeProject: activeProjectReducer }}
        >
          <Resource name="projects" 
            list={ProjectList} 
            show={ProjectShow} 
            edit={ProjectEdit} 
            create={ProjectCreate} 
            icon={BusinessCenter} 
            />
          <Resource name="experiments" 
            list={ExperimentList} 
            edit={ExperimentEdit} 
            create={ExperimentCreate} 
            icon={ExperimentIcon}
            />
          <Resource name="users" 
            list={UserList}  
            icon={UserIcon} />
        </Admin>
      </ProjectContext.Provider>
    );
  
  }
}
    
export default App;