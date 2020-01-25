import React, { Component } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { withRouter } from "react-router";
import { parse, stringify } from "query-string";

import Select from "@material-ui/core/Select";
import MenuItem from "@material-ui/core/MenuItem";

import { setActiveProject as setActiveProjectAction } from "../../../context/entities/projectContext";
import { setActiveExperiment as setActiveExperimentAction } from "../../../context/entities/experimentContext";

class EntitySelect extends Component {
  state = {
    data: []
  };

  getEntityList = query => {
    const {
      props: { entity }
    } = this;

    fetch(`http://35.227.124.46:8080/${entity}s?${stringify(query)}`, {
      method: "GET"
    })
      .then(r => r.json())
      .then(res =>
        this.setState({
          data: res
        })
      )
      .catch(err => console.log(err));
  };

  componentDidMount() {
    const {
      props: {
        entity,
        setActiveProject,
        setActiveExperiment,
        history,
        location: { pathname, search }
      },
      getEntityList
    } = this;

    const { project_id = 1, experiment_id = 0 } = parse(search);

    const params = { project_id, experiment_id };

    const tempObj = JSON.stringify(params);

    localStorage.setItem("current_entities", tempObj);

    history.push(`${pathname}?${stringify(params)}`);

    switch (entity) {
      case "project":
        getEntityList();

        setActiveProject(project_id);
        break;
      case "experiment":
        getEntityList({ project_id });

        setActiveExperiment(experiment_id);
        break;
      default:
        break;
    }
  }

  componentDidUpdate(prevProps, prevState, snapshot) {
    const {
      props: {
        entity,
        activeProjectId,
        setActiveExperiment,
        location: { pathname, search },
        history
      },
      getEntityList
    } = this;

    if (
      entity === "experiment" &&
      prevProps.activeProjectId &&
      prevProps.activeProjectId !== activeProjectId
    ) {
      getEntityList({ project_id: activeProjectId });

      setActiveExperiment(0);
      localStorage.setItem(
        "current_entities",
        JSON.stringify({
          ...parse(search),
          [`experiment_id`]: 0
        })
      );

      const currentEntities = JSON.parse(
        localStorage.getItem("current_entities")
      );

      history.push(`${pathname}?${stringify(currentEntities)}`);
    }
  }

  handleChange = event => {
    const {
      props: {
        entity,
        setActiveProject,
        setActiveExperiment,
        history,
        location: { pathname, search }
      }
    } = this;

    const activeEntityId = event.target.value;

    localStorage.setItem(
      "current_entities",
      JSON.stringify({
        ...parse(search),
        [`${entity}_id`]: activeEntityId
      })
    );

    const currentEntities = JSON.parse(
      localStorage.getItem("current_entities")
    );

    history.push(`${pathname}?${stringify(currentEntities)}`);

    switch (entity) {
      case "project":
        setActiveProject(activeEntityId);
        break;
      case "experiment":
        setActiveExperiment(activeEntityId);
        break;
      default:
        break;
    }
  };

  getCurrentEntityValue = () => {
    const {
      props: { entity, activeProjectId, activeExperimentId }
    } = this;

    switch (entity) {
      case "project":
        return activeProjectId;
      case "experiment":
        return activeExperimentId;
      default:
        return null;
    }
  };

  render() {
    const {
      props: { entity },
      state: { data },
      getCurrentEntityValue
    } = this;

    return (
      <Select value={getCurrentEntityValue()} onChange={this.handleChange}>
        {data &&
          data.map(item => (
            <MenuItem key={item.id} value={item.id}>
              {`${entity} ${item.id}`}
            </MenuItem>
          ))}
      </Select>
    );
  }
}

EntitySelect.propTypes = {
  query: PropTypes.object,
  entity: PropTypes.string,
  activeProjectId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  activeExperimentId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  setActiveProject: PropTypes.func,
  setActiveExperiment: PropTypes.func
};

const mapStateToProps = state => ({
  activeProjectId: state.activeProject,
  activeExperimentId: state.activeExperiment
});

const mapDispatchToProps = dispatch => ({
  setActiveProject: projectId => dispatch(setActiveProjectAction(projectId)),
  setActiveExperiment: experimentId =>
    dispatch(setActiveExperimentAction(experimentId))
});

export default withRouter(
  connect(
    mapStateToProps,
    mapDispatchToProps
  )(EntitySelect)
);
