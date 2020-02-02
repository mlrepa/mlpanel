import React from "react";
import { connect } from "react-redux";
import { List, Datagrid, TextField, ShowButton } from "react-admin";

import FormattedDateField from "../../../shared/FormattedDateField";

const RunList = props => {
  const { activeProjectId, activeExperimentId, dispatch, ...restProps } = props;

  const params = JSON.parse(localStorage.getItem("current_entities"));

  return (
    <List {...restProps} bulkActionButtons={false} filter={params}>
      <Datagrid>
        <TextField label="Run" source="id" />
        <TextField label="Status" source="info.status" />
        <TextField label="Lifecycle stage" source="info.lifecycle_stage" />
        <FormattedDateField innerProp="info" source="start_time" />
        <FormattedDateField innerProp="info" source="end_time" />
        <ShowButton />
      </Datagrid>
    </List>
  );
};

export default connect(state => ({
  activeProjectId: state.activeProject,
  activeExperimentId: state.activeExperiment
}))(RunList);
