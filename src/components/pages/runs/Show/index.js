import React from "react";
import {
  Show,
  SimpleShowLayout,
  TopToolbar,
  ListButton,
  TextField,
} from "react-admin";

import FormattedDateField from "../../../shared/FormattedDateField";

const RunTitle = ({ record }) => {
  return <span>{`Run ${record ? `"${record.info["run_id"]}"` : ""}`}</span>;
};

const RunShowActions = ({ basePath }) => (
  <TopToolbar>
    <ListButton basePath={basePath} />
  </TopToolbar>
);

const RunShow = props => {
  return (
    <Show actions={<RunShowActions />} title={<RunTitle />} {...props}>
      <SimpleShowLayout>
        <TextField label="Run" source="id" />
        <TextField label="Status" source="info.status" />
        <TextField label="Lifecycle stage" source="info.lifecycle_stage" />
        <FormattedDateField innerProp="info" source="start_time" />
        <FormattedDateField innerProp="info" source="end_time" />
      </SimpleShowLayout>
    </Show>
  );
};

export default RunShow;
