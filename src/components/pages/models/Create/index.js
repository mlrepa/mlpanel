import React from "react";
import {
  SimpleForm,
  TextInput,
  Create,
  TopToolbar,
  ListButton
} from "react-admin";

const ExperimentCreateActions = ({ basePath }) => (
  <TopToolbar>
    <ListButton basePath={basePath} />
  </TopToolbar>
);

const ExperimentCreate = props => (
  <Create actions={<ExperimentCreateActions />} {...props}>
    <SimpleForm>
      <TextInput source="name" />
      <TextInput multiline source="description" />
    </SimpleForm>
  </Create>
);

export default ExperimentCreate;
