import React from "react";
import {
  Show,
  SimpleShowLayout,
  TopToolbar,
  ListButton,
  TextField,
  UrlField,
  DeleteButton
} from "react-admin";

import FormattedDateField from "../../../shared/FormattedDateField";

const ExperimentTitle = ({ record }) => {
  return <span>{`Experiment ${record ? `"${record.name}"` : ""}`}</span>;
};

const ExperimentShowActions = ({ basePath, data, resource }) => (
  <TopToolbar>
    <ListButton basePath={basePath} />
    <DeleteButton basePath={basePath} record={data} resource={resource} />
  </TopToolbar>
);

const ExperimentShow = props => (
  <Show
    actions={<ExperimentShowActions />}
    title={<ExperimentTitle />}
    {...props}
  >
    <SimpleShowLayout>
      <TextField source="project_id" />
      <TextField source="name" />
      <FormattedDateField source="creation_time" />
      <FormattedDateField source="last_update_time" />
      <UrlField source="artifact_location" />
      <TextField source="lifecycle_stage" />
      <TextField source="description" />
    </SimpleShowLayout>
  </Show>
);

export default ExperimentShow;
