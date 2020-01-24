import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { formValueSelector } from 'redux-form';
import Button from '@material-ui/core/Button';
import ThumbUp from '@material-ui/icons/ThumbUp';
import { translate, Mutation } from 'react-admin';
import compose from 'recompose/compose';

const sideEffects = {
    onSuccess: {
        notification: {
            body: 'resources.projects.notification.approved_success',
            level: 'info',
        },
        // redirectTo: '/projects',
    },
    onFailure: {
        notification: {
            body: 'resources.projects.notification.approved_error',
            level: 'warning',
        },
    },
};

const ActivateButton = ({ record, translate }) =>
    record && record.status === 'pending' ? (
        <Mutation
            type="UPDATE"
            resource="projects"
            payload={{ id: record.id, data: { status: 'running' } }}
            options={sideEffects}
        >
            {approve => (
                <Button
                    variant="outlined"
                    color="primary"
                    size="small"
                    onClick={approve}
                >
                    <ThumbUp
                        color="primary"
                        style={{ paddingRight: '0.5em', color: 'green' }}
                    />
                    {translate('resources.projects.action.accept')}
                </Button>
            )}
        </Mutation>
    ) : (
        <span />
    );

ActivateButton.propTypes = {
    record: PropTypes.object,
    comment: PropTypes.string,
    translate: PropTypes.func,
};

const selector = formValueSelector('record-form');

const enhance = compose(
    translate,
    connect(state => ({
        comment: selector(state, 'comment'),
    }))
);

export default enhance(ActivateButton);
