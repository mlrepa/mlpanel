import React from "react";
import { connect } from "react-redux";
import {
  List,
  Datagrid,
  TextField,
  ReferenceField,
  EditButton,
  Edit,
  SimpleForm,
  ReferenceInput,
  TextInput,
  SelectInput,
  Create
} from "react-admin";

const ExperimentTitle = ({ record }) => {
  return <span>Experiment {record ? `"${record.title}"` : ""}</span>;
};

const ExperimentListDisconnected = props => {
  const { activeProjectId, ...restProps } = props;
  console.log("activeProjectId", activeProjectId);
  return (
    <div>
      <h3>{`Current propject: ${activeProjectId}`}</h3>
      <List {...restProps} filter={{ project_id: activeProjectId }}>
        <Datagrid
        // data={keyBy(record, 'experiment_id')}
        // ids={experiment_id}
        //
        >
          <ReferenceField source="project_id" reference="projects">
            <TextField source="project_id" />
          </ReferenceField>
          {/* <ReferenceField source="user_id" reference="users"><TextField source="id" /></ReferenceField> */}
          <TextField source="name" />
          {/* <TextField source="artifact_location" /> */}
          <TextField source="lifecycle_stage" />
          <TextField source="last_update_time" /> {/* TODO: DateField */}
          <TextField source="creation_time" /> {/* TODO: DateField */}
          {/* <TextField source="description" /> */}
          <EditButton />
        </Datagrid>
      </List>
    </div>
  );
};

export const ExperimentList = connect(state => ({
  activeProjectId: state.activeProject
}))(ExperimentListDisconnected);

// export const ExperimentEdit = props => (
//     <Edit title={<ExperimentTitle />} {...props}>
//         <SimpleForm>
//             <TextInput source="id" />
//             <ReferenceInput source="userId" reference="users">
//                 <SelectInput optionText="name" />
//             </ReferenceInput>
//             <TextInput source="name" />
//             <TextInput multiline source="body" />
//         </SimpleForm>
//     </Edit>
// );

export const ExperimentEditDisconnected = props => {
  const { activeProjectId, ...restProps } = props;
  console.log("activeProjectId", activeProjectId);

  return (
    <div>
      <Edit
        title={<ExperimentTitle />}
        // {...props}
        {...restProps}
        filter={{ project_id: activeProjectId }}
      >
        <SimpleForm>
          <TextInput source="id" />
          <ReferenceInput source="userId" reference="users">
            <SelectInput optionText="name" />
          </ReferenceInput>
          <TextInput source="name" />
          <TextInput multiline source="body" />
        </SimpleForm>
      </Edit>
    </div>
  );
};

export const ExperimentEdit = connect(state => ({
  activeProjectId: state.activeProject
}))(ExperimentEditDisconnected);

export const ExperimentCreate = props => (
  <Create {...props}>
    <SimpleForm>
      <ReferenceInput source="userId" reference="users">
        <SelectInput optionText="name" />
      </ReferenceInput>
      <TextInput source="name" />
      <TextInput multiline source="body" />
    </SimpleForm>
  </Create>
);
