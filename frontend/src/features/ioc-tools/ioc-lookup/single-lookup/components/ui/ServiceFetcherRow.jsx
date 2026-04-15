import React, { useMemo } from 'react';
import ServiceResultRow from './ServiceResultRow.jsx';
import { useServiceFetcher } from '../../hooks/api/useServiceFetcher';

function ServiceFetcherRow({ ioc, iocType, serviceConfigEntry }) {
  const { loading, apiResult, displayProps } = useServiceFetcher(ioc, iocType, serviceConfigEntry);

  const serviceForChild = useMemo(() => ({
    name: serviceConfigEntry?.name || 'Unknown Service',
    icon: serviceConfigEntry?.icon || 'default_icon',
    detailComponent: serviceConfigEntry?.detailComponent,
  }), [serviceConfigEntry?.name, serviceConfigEntry?.icon, serviceConfigEntry?.detailComponent]);

  return (
    <ServiceResultRow
      serviceKey={serviceConfigEntry?.key || serviceConfigEntry?.name}
      service={serviceForChild}
      loading={loading}
      result={apiResult}
      summary={displayProps.summary}
      tlp={displayProps.tlp}
      ioc={ioc}
      iocType={iocType}
    />
  );
}

export default React.memo(ServiceFetcherRow);
