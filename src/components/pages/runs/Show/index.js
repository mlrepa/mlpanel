import React from "react";
import {
  Show,
  SimpleShowLayout,
  TopToolbar,
  ListButton,
  TextField,
  ArrayField,
  NumberField,
  Datagrid,
  UrlField,
  DeleteButton
} from "react-admin";

import FormattedDateField from "../../../shared/FormattedDateField";

const RunTitle = ({ record }) => {
  return <span>{`Run ${record ? `"${record.info["run_id"]}"` : ""}`}</span>;
};

const RunShowActions = ({ basePath, data, resource }) => (
  <TopToolbar>
    <ListButton basePath={basePath} />
    <DeleteButton basePath={basePath} record={data} resource={resource} />
  </TopToolbar>
);

const RunShow = props => {
  return (
    <Show actions={<RunShowActions />} title={<RunTitle />} {...props}>
      <SimpleShowLayout>
        <TextField label="Run" source="id" />
        <UrlField label="Artifact URI" source="info.artifact_uri" />
        <TextField label="Status" source="info.status" />
        <TextField label="Lifecycle stage" source="info.lifecycle_stage" />
        <FormattedDateField innerProp="info" source="start_time" />
        <FormattedDateField innerProp="info" source="end_time" />
        <ArrayField label="Metrics" source="data.metrics">
          <Datagrid>
            <TextField source="key" />
            <NumberField source="value" />
            <FormattedDateField source="timestamp" />
            <TextField source="step" />
          </Datagrid>
        </ArrayField>
        <ArrayField label="Params" source="data.params">
          <Datagrid>
            <TextField source="key" />
            <NumberField source="value" />
          </Datagrid>
        </ArrayField>
        <ArrayField label="Tags" source="data.tags">
          <Datagrid>
            <TextField source="key" />
            <NumberField source="value" />
          </Datagrid>
        </ArrayField>
      </SimpleShowLayout>
    </Show>
  );
};

export default RunShow;
