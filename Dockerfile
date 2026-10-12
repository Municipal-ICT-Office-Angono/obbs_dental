FROM odoo:19

USER root

# Install openpyxl (required by obbs_dental for DOH Form 2 Excel report generation)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3-openpyxl \
        python3-pip \
    && (pip3 install --no-cache-dir --break-system-packages openpyxl || true) \
    && rm -rf /var/lib/apt/lists/*

# Production entrypoint wrapper
COPY config/entrypoint.sh /entrypoint-prod.sh
RUN chmod +x /entrypoint-prod.sh

USER odoo

ENTRYPOINT ["/entrypoint-prod.sh"]
CMD ["odoo"]
