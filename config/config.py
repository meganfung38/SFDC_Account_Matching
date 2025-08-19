import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Comprehensive list of bad email domains
# Combines existing domains from codebase with domains from bad_domains_latest_2025_01_27.csv
BAD_EMAIL_DOMAINS = {
    # Existing domains from codebase
    'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com',
    'protonmail.com', 'zoho.com', 'aol.com', 'live.com', 'msn.com',
    'ymail.com', 'rocketmail.com', 'me.com', 'mac.com', 'yahoo.co.uk', 
    'yahoo.ca', 'yahoo.com.au', 'googlemail.com', 'mail.com', 'yandex.com', 
    'gmx.com', 'inbox.com', 'fastmail.com', 'tutanota.com', 'guerrillamail.com', 
    '10minutemail.com', 'mailinator.com', 'tempmail.org', 'dispostable.com', 
    'throwaway.email',
    
    # Additional domains from bad_domains_latest_2025_01_27.csv
    'comcast.net', 'verizon.netm', 'rogers.com', 'earthlink.net', 'cox.net', 
    'netzero.com', 'bell.net', 'fastmail.net', 'none.com', 'bellsouth.net', 
    'ringcentral.com', 'att.com', 'test.com', 'verizon.net', 'comcast.com',
    'rr.com', 'sbcglobal.net', 'optonline.net', 'windstream.com', 'live.ca',
    'hotmail.ca', 'shaw.ca', 'charter.net', 'ringcentralbusiness.com',
    'swbell.net', 'att.net', 'email.com', 'no.com', 'no.comx', 'no.no', 
    'noeamil.com', 'noemail.com', 'qwest.net', 'qwestoffice.net', 'rc.com', 
    'testmail.com', 'verizon.com', 'verizon.et', 'verizon.ne', 'verizone.net',
    'wirelessadvisors.ca', 'wireless-systems.net', 'a.com', '126.com', '163.com',
    '123.com', '1.com', 'qq.com', 'eastlink.ca', 'hushmail.com', 'snet.net',
    'netzero.net', 'belnet.ca', 'netscape.net', 'sympatico.ca', 'telus.com', 
    'juno.com', 'btiniternet.com', 'roadrunner.com', 'pacbell.net', 'windstream.net', 
    'mindspring.com', 'kc.rr.com', 'telus.net', 'sky.com', 'btconnect.com', 
    'bt.com', 'btinternet.com', 'btopenworld.com', 'hotmail.co.uk', 'wi.rr.com', 
    'panhandle.rr.com', 'yahooo.com', 'yahoo.comgeek', 'noneonyahoosearch.com', 
    'san.rr.com', 'od.ab-soft.net', 'nordigy.ru', 'godaddy.com', 'bell.ca', 
    'test.co.uk', 'abc.com', 'bouyguestelecom.fr', 'dartybox.com', 'fdn.fr', 
    'free.fr', 'grenoblix.net', 'caissedesdepots.fr', 'lyonix.net', 'neufcegetel.fr', 
    'orange.fr', 'orange.com', 'sfr.fr', 'wanadoo.fr', 'yopmail.com', 'simplion.com', 
    'facebook.com', 'cox.com', 'comcastspectacor.com', 'sprint.com', 'charter.com', 
    'vecc9-1-1.com', 'c-and-a.com', 'atlantic-me.com', 'id-a.com', 'i-sprint.com', 
    'j-l-a.com', 'health.msn.com', 'ifi-test.com', 'qi-a.com', 'fn-test.com', 
    'riflechurch.qwestoffice.net', 'redcare.bt.com', 'ami-me.com', 'image-1.com',
    'giordano-me.com', 'san-a.com', 'mgc-a.com', 'hol-mac.com', 'charter-a.com',
    'bus-charter.com', 'outlook.live.com', 'american-1.com', 'e-t-a.com',
    'corporate.charter.com', 'frsky-rc.com', 'bt.com.au', 'jet-mail.com',
    'sdf-a.com', 'sales-email.com', 'aa-me.com', 'ec.rr.com', 'csc-a.com', 
    'j-m-a.com', 'ps.ringcentral.com', 'canvas-sky.com', 'retire-me.com',
    'b-n-a.com', 'advantage-rc.com', 'jive-live.com', 'interstate-1.com',
    'era-rc.com', 'cfl.rr.com', 'hawkeye-1.com', 'usa-rc.com', 'yb-a.com', 
    'secureweb-mail.com', 'taa-a.com', 'sc.rr.com', 'hot.rr.com', 'ltcreit.rc.com', 
    'woh.rr.com', 'vip.126.com', 'live.com.mx', 'elva-1.com', 'facebook.com.au', 
    'graham-rogers.com', 'lac-mac.com', 'alaska-fishing-charter.net', 'cts-1.com', 
    'sky.com.mx', 'corporate.comcast.com', 'ocean-yacht-charter.com', 'lj-a.com', 
    'bank-abc.com', 'annie-mac.com', 'h-mac.com', 'sport.uk.msn.com', 'compu-mail.com',
    'ccclients-test.com', 'portal-a.com', 'star-1.com', 'all-and-1.com', 'marsm-a.com',
    'esg-1.com', 'ic-1.com', 'n-a-f-a.com', 'champion-charter.com', 'bonfire-live.com',
    'bengamla-charter.com', 'dyna-mac.com', 'data-mail.com', 'for-a.com', 'tube-mac.com',
    'mst-1.com', 'wg-a.com', 'method-1.com', 'sky.com.br', 'isb-me.com', 'cybersecurity.att.com',
    'tru-test.com', 'm-f-a.com', 'trans-1.com', 'autism-live.com', 'the-mac.com',
    'itc-1.com', 'new.rr.com', 'cinci.rr.com', 'chick-fil-a.com', 'nycap.rr.com',
    'live-live.com', 'mood-me.com', 'sch-a.com', 'knight-sky.com', 'pss-1.com',
    '0-to-1.com', 'yahoo.com.tw', 'hazmat-1.com', 'asia-mail.com', 'msi-me.com',
    'automation-123.com', 'austin.rr.com', 'mms.att.net', 'tampabay.rr.com',
    'bar-a.com', 'rai-1.com', 'live.com.au', 'm-rr.com', 'rooftech-no.com',
    'jzw-a.com', 'perfect-live.com', 'option-1.com', 'alaska-charter.com',
    'eco-mail.com', 'merri-mac.com', 'mmp-a.com', 'm-n-a.com', 'total-mail.com',
    'nj.rr.com', 'roger-cox.com', 'nic-mail.com', 'ati-1.com', 'alpha-1.com',
    'digital-outlook.com', 'maynards-rogers.com', 'fpi-no.com', 'nc.rr.com',
    'bci-1.com', '60601-1.com', 'balance-me.com', 'market-outlook.com', 'p-m-a.com',
    'pei-1.com', 'rcs-rc.com', 'lj-rogers.com', 'model-a.com.au', 'sae-a.com',
    'honest-1.com', 'efp-me.com', 'intraco-me.com', 'moore-me.com', 'ajk-a.com',
    'hl-a.com', 'n-o-v-a.com', 'architecture-1.com', 'jm-a.com', 'all-in-1.com',
    'second-to-none.com', 'robin-rogers.com', 'jor-mac.com', 'bma-1.com',
    'alert-1.com', 'plumbers-1.com', 'stellar-1.com', 'packard-1.com', 'sdt-1.com',
    'intercon-1.com', 'au.news.yahoo.com', 'project-a.com', 'nea-me.com',
    'servicemaster-rc.com', 'rtv-live.com', 'redshift-live.com', 'indy-live.com',
    'photo-me.com', 'express-1.com', 'globalservices.bt.com', 'ilr-mail.com',
    'ccs-live.com', 'ocb-me.com', 'protransport-1.com', 'opx-1.com', 'icam-1.com',
    'ver-mac.com', 'consolidated-mail.com', 'techno-test.com', 'members.aol.com',
    'cincinnati-test.com', 'l-p-a.com', 'huntingtonloans-email.com', 'bds-1.com',
    'wp-a.com', 'b-w-a.com', 'ca.rr.com', 'executive-email.com', 'o-plus-a.com',
    'k-a.com', 'amr-no.com', 'usnet-1.com'
}

class Config:
    """Base configuration class"""
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Salesforce Configuration
    SF_USERNAME = os.getenv('SF_USERNAME')
    SF_PASSWORD = os.getenv('SF_PASSWORD')
    SF_SECURITY_TOKEN = os.getenv('SF_SECURITY_TOKEN')
    SF_DOMAIN = os.getenv('SF_DOMAIN', 'login')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
    
    @staticmethod
    def validate_salesforce_config():
        """Validate that all required Salesforce credentials are present"""
        required_vars = ['SF_USERNAME', 'SF_PASSWORD', 'SF_SECURITY_TOKEN']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
    
    @staticmethod
    def validate_openai_config():
        """Validate that OpenAI API key is present"""
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("Missing required environment variable: OPENAI_API_KEY")
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 