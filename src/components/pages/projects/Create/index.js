import React from "react";
import {
  SimpleForm,
  TextInput,
  Create,
  TopToolbar,
  ListButton
} from "react-admin";

const ProjectCreateActions = ({ basePath }) => (
  <TopToolbar>
    <ListButton basePath={basePath} />
  </TopToolbar>
);

const ProjectCreate = props => (
  <Create actions={<ProjectCreateActions />} {...props}>
    <SimpleForm>
      <TextInput label="Project name" source="project" />
    </SimpleForm>
  </Create>
);

export default ProjectCreate;
